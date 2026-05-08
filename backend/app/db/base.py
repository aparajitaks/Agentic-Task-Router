"""
app/db/base.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    SQLAlchemy needs a single "declarative base" class from which all ORM
    models inherit.  Keeping it here (separate from session.py) prevents
    circular imports when models and session logic reference each other.

WHAT IT DOES
    - Defines `Base` — the declarative base for all SQLAlchemy models
    - Defines `TimestampMixin` — a reusable mixin that adds created_at /
      updated_at columns to any model automatically
    - `__table_args__` with `extend_existing=True` allows Alembic to detect
      tables safely during autogenerate

HOW IT CONNECTS
    app/models/task.py    → inherits from Base, TimestampMixin
    app/models/agent.py   → inherits from Base, TimestampMixin
    app/models/log.py     → inherits from Base
    alembic/env.py        → imports Base.metadata to detect all tables
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Return a timezone-aware UTC datetime. Prefer this over datetime.utcnow()."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base.

    All ORM model classes must inherit from this Base so Alembic can discover
    them via Base.metadata and generate migrations automatically.
    """
    pass


class TimestampMixin:
    """
    Mixin that adds audit timestamp columns to any model.

    Columns:
        created_at  — set once on INSERT, never updated
        updated_at  — set on INSERT and updated on every UPDATE via onupdate

    Both are stored in UTC without tzinfo (PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
    to keep them database-agnostic while still being deterministic.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=_utcnow,
        server_default=func.now(),   # DB-level default as safety net
        nullable=False,
        index=True,                  # Common query: "tasks created after X"
        doc="UTC timestamp when the record was first created.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=_utcnow,
        server_default=func.now(),
        onupdate=_utcnow,            # Automatically updated on every UPDATE
        nullable=False,
        doc="UTC timestamp of the last modification.",
    )
