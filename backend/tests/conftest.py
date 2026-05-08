"""
tests/conftest.py
─────────────────────────────────────────────────────────────────────────────
pytest fixtures for the Agentic Task Router test suite.

Key design decisions:
- Uses SQLite in-memory (aiosqlite) for speed — no real Postgres needed
- Each test gets freshly created + dropped tables (function scope)
- FastAPI's get_db dependency is overridden to use the test session
- The deprecated custom event_loop fixture is removed; pytest-asyncio 0.24+
  manages the event loop automatically via asyncio_mode = auto
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app

# ─────────────────────────────────────────────────────────────────────────────
# Test Database Setup
# ─────────────────────────────────────────────────────────────────────────────
# SQLite in-memory for speed.
# StaticPool + check_same_thread=False are required for async SQLite.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    Create all tables before each test, drop them after.

    autouse=True → runs automatically for every test function.
    scope="function" → each test gets a clean slate (no cross-test pollution).
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean database session per test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an async HTTP test client wired to the FastAPI app.

    Overrides get_db so routes use the test DB session instead of
    the real PostgreSQL database.
    """
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
