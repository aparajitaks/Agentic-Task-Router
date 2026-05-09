"""
app/main.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This is the application entry point — the file that:
      1. Creates the FastAPI application instance
      2. Registers all middleware
      3. Registers all routers
      4. Registers all exception handlers
      5. Manages startup and shutdown lifecycle events

    Everything is assembled here but none of the logic lives here.

WHAT IT DOES
    - Creates a FastAPI app with metadata (title, version, docs URL)
    - Uses `@asynccontextmanager` lifespan to handle startup (init_db)
      and shutdown (close_db) gracefully
    - Adds CORS middleware (allows the frontend to call the API)
    - Adds custom request logging middleware
    - Includes versioned API routers under /api/v1
    - Registers global exception handlers

HOW IT CONNECTS
    All other modules converge here:
      app/config/settings.py   → get_settings() for app metadata and CORS
      app/db/session.py        → init_db(), close_db() called in lifespan
      app/core/logging.py      → configure_logging() called at startup
      app/core/exceptions.py   → register_exception_handlers(app)
      app/routes/health.py     → health_router
      app/routes/tasks.py      → tasks_router
      app/utils/middleware.py  → RequestLoggingMiddleware
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.session import close_db, init_db
from app.routes import (
    health_router, 
    tasks_router, 
    gmail_router, 
    tools_router, 
    approvals_router,
    users_router
)
from app.utils.middleware import RequestLoggingMiddleware

settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# Lifespan (Startup / Shutdown)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan handler.

    Code before `yield` runs on startup.
    Code after `yield` runs on shutdown.

    This replaces the deprecated @app.on_event("startup") pattern.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.app_env)
    await init_db()
    logger.info("Application startup complete.")
    logger.info("CORS Allowed Origins: %s", settings.cors_origins)
    logger.info("=" * 60)

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down %s...", settings.app_name)
    await close_db()
    logger.info("Shutdown complete.")


# ─────────────────────────────────────────────────────────────────────────────
# Application Factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Application factory — creates and fully configures the FastAPI instance.

    Using a factory function (instead of a module-level `app = FastAPI()`)
    makes the app easier to test:
        from app.main import create_app
        test_client = TestClient(create_app())
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Production-grade Agentic Task Router backend. "
            "Designed to support AI agents, LangGraph workflows, "
            "Gmail integration, and multi-agent orchestration."
        ),
        docs_url="/docs" if not settings.is_production else None,   # Disable Swagger in prod
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    # CORS is added LAST because middleware is processed in reverse order.
    # This makes CORS the outermost layer, handling preflights immediately.

    app.add_middleware(RequestLoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    # Health check is at the root level (no /api/v1 prefix) for simplicity
    app.include_router(health_router)

    # All feature routes are versioned under /api/v1
    app.include_router(tasks_router, prefix=settings.api_v1_prefix)
    app.include_router(gmail_router, prefix=settings.api_v1_prefix)
    app.include_router(tools_router, prefix=settings.api_v1_prefix)
    app.include_router(approvals_router, prefix=settings.api_v1_prefix)
    app.include_router(users_router, prefix=settings.api_v1_prefix)

    return app


# ─────────────────────────────────────────────────────────────────────────────
# WSGI/ASGI Entry Point
# ─────────────────────────────────────────────────────────────────────────────
# This module-level `app` is what uvicorn looks for when you run:
#   uvicorn app.main:app --reload
app = create_app()
