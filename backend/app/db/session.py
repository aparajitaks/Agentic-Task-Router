"""
app/db/session.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Database connections are expensive.  This module manages an async
    SQLAlchemy connection pool so every request reuses existing connections
    instead of opening a new one.  It also provides the FastAPI dependency
    that injects an async DB session into route handlers.

WHAT IT DOES
    1. Creates an async engine (asyncpg driver for PostgreSQL)
    2. Creates an async session factory (AsyncSessionLocal)
    3. Exposes `get_db()` — an async generator used with FastAPI's Depends()
       so each request gets its own session that is automatically committed
       or rolled back and closed when the request finishes.

HOW IT CONNECTS
    app/main.py            → calls init_db() / close_db() in lifespan
    app/routes/tasks.py    → db: AsyncSession = Depends(get_db)
    app/services/task.py   → receives the session as a parameter
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# Async Engine
# ─────────────────────────────────────────────────────────────────────────────
# pool_pre_ping=True  — test connections before handing them out (avoids
#                        "SSL connection has been closed unexpectedly" errors)
# pool_size=10        — keep 10 connections alive at all times
# max_overflow=20     — allow up to 20 extra temporary connections under load
# echo               — log SQL statements only in DEBUG mode (never in prod)
engine_args = {
    "pool_pre_ping": True,
    "echo": settings.debug,
    "future": True,
}
if not settings.database_url.startswith("sqlite"):
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_async_engine(
    settings.database_url,
    **engine_args
)

# ─────────────────────────────────────────────────────────────────────────────
# Session Factory
# ─────────────────────────────────────────────────────────────────────────────
# expire_on_commit=False — keeps ORM objects accessible after the commit so
#                          we can serialize them to JSON without extra queries
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,   # We flush manually before queries that need fresh data
    autocommit=False,  # Always explicit — never auto-commit
)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Dependency
# ─────────────────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...

    The `async with` block guarantees:
        - If the route completes normally → session.commit() is called
        - If an exception is raised      → session.rollback() is called
        - Always                         → session.close() is called
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle Helpers (called from main.py lifespan)
# ─────────────────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Verify the database connection on startup.

    NOTE: We do NOT call Base.metadata.create_all() here.
          Table creation is handled exclusively by Alembic migrations.
    """
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity check passed.")
    except Exception as e:
        # Non-fatal: log and continue — the DB may not be reachable yet during
        # Docker Compose startup sequencing (health check will catch real failures)
        logger.warning("Database connectivity check failed: %s", e)

    logger.info("Database engine initialised.")


async def close_db() -> None:
    """Dispose the connection pool gracefully on shutdown."""
    await engine.dispose()
    logger.info("Database connection pool disposed.")
