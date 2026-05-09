"""
app/models/approval.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Human-in-the-loop workflows require a durable record of every approval
    decision made about a piece of AI-generated content. This model stores
    the full approval lifecycle — from when the AI pauses to wait for review,
    to what the human decided, when they decided it, and what they changed.

    It is the auditability backbone of enterprise AI governance.

WHAT IT DOES
    - Defines `Approval`: the core record created when a workflow reaches a
      HITL checkpoint and needs a human decision.
    - Defines `ApprovalStatus`: the state machine governing the decision lifecycle.
    - Stores the AI-generated draft so the human sees exactly what the agent produced.
    - Stores the human-edited version (if edited) for full diff traceability.
    - Stores the serialized LangGraph checkpoint state so execution can resume
      from exactly the right point.

HOW IT CONNECTS
    - app/models/task.py    → Each Approval belongs to one Task (FK relationship)
    - app/services/approval.py → CRUD layer for querying/updating approvals
    - app/routes/approvals.py  → REST API exposing approval management
    - app/graphs/main_graph.py → Graph checks for pending approvals at the HITL node
    - frontend/approvals page  → Polls GET /approvals and renders the review queue
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class ApprovalStatus(str, enum.Enum):
    """
    The state machine for a HITL approval record.

    PENDING_APPROVAL → Initial state. Workflow is paused. Human has not acted.
    APPROVED         → Human reviewed and confirmed the AI output as-is.
    EDITED           → Human reviewed, modified the content, and approved the edit.
    REJECTED         → Human rejected the AI output. Workflow will be terminated
                       or escalated based on policy.
    EXPIRED          → No human action within the SLA window. Triggers auto-policy.
    """
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalPolicy(str, enum.Enum):
    """
    Governs WHAT triggers an approval gate.

    ALWAYS         → Every workflow hitting this node requires human review.
    EMAIL_EXTERNAL → Only workflows sending to external domains require review.
    HIGH_RISK      → Only flagged high-risk actions require review.
    DISABLED       → HITL is disabled; workflows proceed autonomously.
    """
    ALWAYS = "always"
    EMAIL_EXTERNAL = "email_external"
    HIGH_RISK = "high_risk"
    DISABLED = "disabled"


class Approval(Base, TimestampMixin):
    """
    Represents a single human-review checkpoint in an agentic workflow.

    When the LangGraph workflow reaches the `human_review_node`, it:
    1. Serializes its current state into `graph_checkpoint_state`.
    2. Creates an `Approval` record with PENDING_APPROVAL status.
    3. Pauses execution — the Celery task finishes, the workflow is frozen.

    When a human acts via the API, the service:
    1. Updates this record with the decision + timestamp.
    2. Enqueues a new Celery task to RESUME the graph from the checkpoint.

    Table: approvals
    """
    __tablename__ = "approvals"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
        doc="Globally unique approval identifier.",
    )

    # ── Task Link ─────────────────────────────────────────────────────────────
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The task this approval checkpoint belongs to.",
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="The user this approval checkpoint belongs to.",
    )

    # ── AI-Generated Content Under Review ─────────────────────────────────────
    ai_generated_draft: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="The AI-generated content (e.g., email reply) that needs human approval.",
    )

    original_input: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="The original user/email input that triggered this workflow.",
    )

    workflow_context: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Metadata about the workflow at the checkpoint: route, tool calls, agent used, etc.",
    )

    # ── LangGraph Checkpoint ──────────────────────────────────────────────────
    graph_checkpoint_state: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc=(
            "Serialized WorkflowState dict at the moment of pausing. "
            "Used to reconstruct and resume the LangGraph execution."
        ),
    )

    checkpoint_node: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="The LangGraph node name where execution was paused.",
    )

    # ── Decision ──────────────────────────────────────────────────────────────
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus, name="approval_status_enum", create_type=True),
        default=ApprovalStatus.PENDING_APPROVAL,
        nullable=False,
        index=True,
        doc="Current state of the approval decision.",
    )

    human_edited_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="If status=EDITED, this holds the human's corrected version of the AI draft.",
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="If status=REJECTED, the human must provide a reason for audit purposes.",
    )

    # ── Reviewer Identity ─────────────────────────────────────────────────────
    reviewer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Identifier of the human reviewer (email, user ID, etc). Prepared for RBAC.",
    )

    reviewer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Display name of the reviewer for audit log readability.",
    )

    # ── Timing ────────────────────────────────────────────────────────────────
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the human submitted their decision.",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="SLA deadline — if no decision by this time, status transitions to EXPIRED.",
    )

    # ── Resume Tracking ───────────────────────────────────────────────────────
    resumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the workflow was successfully resumed after approval.",
    )

    resume_task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Celery task ID of the resumed workflow execution for traceability.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    task: Mapped[Task] = relationship(
        "Task",
        back_populates="approvals",
        lazy="select",
    )

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="approvals",
        lazy="select",
    )

    # ── Composite Indexes ─────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_approvals_status_created_at", "status", "created_at"),
        Index("ix_approvals_task_status", "task_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Approval id={self.id!s:.8} task_id={self.task_id!s:.8} "
            f"status={self.status.value!r}>"
        )
