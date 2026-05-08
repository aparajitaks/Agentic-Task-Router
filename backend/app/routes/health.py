"""
app/routes/health.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Load balancers, Kubernetes, and Docker Compose health checks all need an
    endpoint that reliably returns 200 when the service is up.  This should
    be the FIRST route tested in CI/CD pipelines and deployment verification.

WHAT IT DOES
    GET /health           → basic liveness check (always returns 200 if app is running)
    GET /api/v1/health/db → readiness check (confirms DB connection is alive)

HOW IT CONNECTS
    app/main.py            → router included in the main app
    Docker HEALTHCHECK     → checks GET /health
    CI/CD pipeline         → checks both endpoints after deployment
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.core.responses import success_response
from app.db.session import get_db

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness Check")
async def health_check() -> dict:
    """
    Basic liveness probe.

    Returns 200 immediately without touching the database.
    Use this for load balancer health checks.
    """
    return success_response(
        data={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        message="Service is running.",
    )


@router.get("/api/v1/health/db", summary="Readiness / DB Check")
async def db_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Readiness probe — verifies the database connection.

    Runs a trivial `SELECT 1` query.  If it succeeds, the app is ready
    to serve traffic.  Returns 500 automatically if the DB is unreachable
    (the unhandled exception handler kicks in).
    """
    start = datetime.now(timezone.utc)
    await db.execute(text("SELECT 1"))
    latency_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000

    logger.debug("DB health check passed | latency=%.2fms", latency_ms)

    return success_response(
        data={
            "status": "healthy",
            "database": "connected",
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        message="Database connection is healthy.",
    )
