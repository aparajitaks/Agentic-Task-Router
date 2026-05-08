"""
app/core/logging.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Scattered print() calls are a debugging anti-pattern.  Production services
    need structured, levelled logging that can be captured by Docker, Datadog,
    CloudWatch, etc.  This module creates a single configured logger that every
    other module imports — ensuring consistent format, level, and handler across
    the entire application.

WHAT IT DOES
    - Reads LOG_LEVEL from Settings
    - Configures the root "app" logger with a StreamHandler (stdout)
    - Formats log lines as:  2026-05-08 22:07:39 | INFO     | app.routes.tasks | message
    - Exposes a get_logger(name) factory so each module gets a properly
      namespaced child logger

HOW IT CONNECTS
    app/main.py          → calls configure_logging() at startup
    Every other module   → calls get_logger(__name__) for a named logger
"""

import logging
import sys

from app.config.settings import get_settings


def configure_logging() -> None:
    """
    Set up the root application logger.

    Called once from app/main.py lifespan on startup so that all child loggers
    inherit the same handler and formatter.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level, logging.INFO)

    # ── Formatter ─────────────────────────────────────────────────────────────
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # ── Handler: write to stdout (Docker captures stdout logs) ────────────────
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # ── Root "app" logger ──────────────────────────────────────────────────────
    root_logger = logging.getLogger("app")
    root_logger.setLevel(level)
    root_logger.handlers.clear()          # Avoid duplicate handlers on hot-reload
    root_logger.addHandler(handler)
    root_logger.propagate = False         # Don't bubble up to the root Python logger

    # Keep uvicorn / sqlalchemy loggers quieter in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named child logger under the "app" namespace.

    Usage:
        logger = get_logger(__name__)
        logger.info("Task created", extra={"task_id": task.id})
    """
    return logging.getLogger(f"app.{name}")
