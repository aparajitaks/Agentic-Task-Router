"""
app/models/task.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The Task is the central domain object of this system.  Every agent action,
    log entry, and workflow step ultimately traces back to a Task.  This model
    is the single source of truth for what a "task" looks like in the database.

WHAT IT DOES
    Defines the `Task` SQLAlchemy ORM model with:
      - Primary key (UUID for global uniqueness, safe to expose in URLs)
      - Status field using a Python Enum so only valid values reach the DB
      - Indexes on status and created_at for common list-query patterns
      - Relationship to Log entries (one Task → many Logs)
      - Soft-delete support via `is_deleted` flag (never hard-delete audit data)

HOW IT CONNECTS
    app/db/base.py         → Base and TimestampMixin inherited here
    app/models/log.py      → references task_id as a FK
    app/schemas/task.py    → serializes Task instances to Pydantic models
    app/services/task.py   → queries and mutates Task rows
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.types import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    # Imported only during type-checking (e.g. Pyrefly, mypy).
    # At runtime SQLAlchemy resolves these string annotations itself,
    # so we avoid circular imports while still satisfying the type checker.
    from app.models.agent import Agent
    from app.models.log import Log


class TaskStatus(str, enum.Enum):
    """
    Lifecycle states a Task moves through.

    Inheriting from `str` means FastAPI/Pydantic can serialize the enum
    as its string value rather than needing a custom encoder.

    PENDING   → Task created, waiting to be picked up by a worker/agent
    IN_PROGRESS → An agent has claimed and started working on it
    COMPLETED → Work finished successfully
    FAILED    → Processing failed; see related Log entries for details
    CANCELLED → Manually cancelled before completion
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base, TimestampMixin):
    """
    Core domain model representing a unit of work in the Agentic Task Router.

    Table: tasks
    """

    __tablename__ = "tasks"

    # ── Primary Key ───────────────────────────────────────────────────────────
    # UUID chosen over sequential int:
    #   - No enumeration attacks (attacker can't guess /tasks/1, /tasks/2)
    #   - Safe to generate client-side or in a distributed system
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
        doc="Globally unique task identifier.",
    )

    # ── Core Fields ───────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Short human-readable title for the task.",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional detailed description of the work to be done.",
    )

    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status_enum", create_type=True),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,           # Frequently filtered: "show me all PENDING tasks"
        doc="Current lifecycle state of the task.",
    )

    # ── Agent Assignment (nullable until an agent claims the task) ────────────
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="The agent currently responsible for this task (if any).",
    )

    # ── Soft Delete ───────────────────────────────────────────────────────────
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Soft-delete flag. Deleted tasks are hidden but never purged.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    logs: Mapped[list[Log]] = relationship(
        "Log",
        back_populates="task",
        cascade="all, delete-orphan",   # Deleting a task deletes its logs
        lazy="select",                  # Load logs only when explicitly accessed
    )

    assigned_agent: Mapped[Agent | None] = relationship(
        "Agent",
        back_populates="tasks",
        lazy="select",
    )

    # ── Composite Indexes ─────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_tasks_status_created_at", "status", "created_at"),
        Index("ix_tasks_agent_status", "assigned_agent_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id!s:.8} title={self.title!r} status={self.status.value!r}>"
