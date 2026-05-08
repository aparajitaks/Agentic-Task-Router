"""
app/models/log.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Immutable audit logs are non-negotiable in agentic systems.  When an
    AI agent fails or produces unexpected output, you need a step-by-step
    trail of everything that happened during a Task's lifetime.

WHAT IT DOES
    - Creates an immutable per-task event log (INSERT only, never UPDATE)
    - Stores log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) for filtering
    - `source` identifies which component created the log (agent, API, worker)
    - `metadata_json` is a flexible JSONB field for structured context

HOW IT CONNECTS
    app/models/task.py           → back-populated via logs relationship
    app/services/task_service.py → creates log entries on state transitions
    Future: Celery workers will write logs as tasks progress
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, JSON, String, Text
from sqlalchemy.types import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    # Imported only during type-checking; at runtime SQLAlchemy resolves
    # "Task" as a string reference, so no circular import occurs.
    from app.models.task import Task


class LogLevel(str, enum.Enum):
    """Maps to standard Python logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Log(Base):
    """
    Immutable event log entry for a Task.

    Design notes:
    - No TimestampMixin because logs have only `timestamp` (insert time).
      They are never updated.
    - JSONB `metadata_json` allows storing arbitrary structured context
      (e.g., agent response payload, tool call arguments).

    Table: logs
    """

    __tablename__ = "logs"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Foreign Key ───────────────────────────────────────────────────────────
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The task this log entry belongs to.",
    )

    # ── Log Content ───────────────────────────────────────────────────────────
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable log message.",
    )

    level: Mapped[LogLevel] = mapped_column(
        SAEnum(LogLevel, name="log_level_enum", create_type=True),
        default=LogLevel.INFO,
        nullable=False,
        index=True,
        doc="Severity level of this log entry.",
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Component that generated this log (e.g. 'gmail-reader-agent', 'api').",
    )

    # ── Flexible Context Storage ──────────────────────────────────────────────
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        doc="Arbitrary JSON context (tool outputs, agent thoughts, etc.).",
    )

    # ── Timestamp ────────────────────────────────────────────────────────────
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
        index=True,
        doc="UTC datetime when this event occurred.",
    )

    # ── Relationship ─────────────────────────────────────────────────────────
    task: Mapped[Task] = relationship(
        "Task",
        back_populates="logs",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Log id={self.id!s:.8} task_id={self.task_id!s:.8} "
            f"level={self.level.value!r} source={self.source!r}>"
        )
