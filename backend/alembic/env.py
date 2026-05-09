"""
alembic/env.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Alembic needs to know:
      1. WHERE the database is (DATABASE_URL)
      2. WHICH tables to manage (Base.metadata)
      3. HOW to run migrations (sync vs async)

    This file configures all three and supports both online (connected) and
    offline (generate SQL scripts only) migration modes.

WHAT IT DOES
    - Reads DATABASE_URL from environment (overrides alembic.ini default)
    - Imports Base.metadata so autogenerate can detect all model changes
    - Supports async migrations using run_sync() around synchronous Alembic calls

HOW IT CONNECTS
    alembic/versions/*.py  → individual migration scripts call op.create_table(), etc.
    app/db/base.py         → Base imported here for metadata
    app/models/*           → All models imported via app.models to populate metadata
"""

import os
from logging.config import fileConfig
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool

# ─────────────────────────────────────────────────────────────────────────────
# Import all models so Alembic can detect them in metadata
# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL: If you add a new model file, also import it in app/models/__init__.py
# so it gets picked up here automatically.
from app.db.base import Base
import app.models  # noqa: F401 — side-effect import to register all models on Base.metadata

# ─────────────────────────────────────────────────────────────────────────────
# Load environment variables from .env
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Alembic Config Object
# ─────────────────────────────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─────────────────────────────────────────────────────────────────────────────
# Target metadata for autogenerate
# ─────────────────────────────────────────────────────────────────────────────
target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Resolve DATABASE_URL from environment (takes priority) or alembic.ini.

    In Docker: DATABASE_URL env var is set.
    Locally:   Falls back to alembic.ini's sqlalchemy.url (uses psycopg2, not asyncpg).
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        # Alembic CLI is synchronous — replace async driver with sync driver
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        url = url.replace("sqlite+aiosqlite://", "sqlite://")
        return url
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("DATABASE_URL not found in environment or alembic.ini")
    return url


def run_migrations_offline() -> None:
    """
    Run migrations in "offline" mode.

    This generates SQL scripts without connecting to the database.
    Useful for reviewing changes before applying them in production.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,       # Detect column type changes
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in "online" mode — connects to the database and applies changes.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # Don't pool — Alembic runs once and exits
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
