"""
app/models/approval.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Enterprise AI requires human governance. We cannot let agents send emails
    autonomously without supervision. This file defines the data models for
    managing human approvals, audits, and workflow checkpoints.

WHAT IT DOES
    Defines two models:
    1. Approval: Tracks human review decisions (Approve, Reject, Edit).
    2. WorkflowCheckpoint: Stores serialized LangGraph execution states so we
       can pause a workflow in a Celery worker, drop the process, and resume
       it later safely from the exact same node.

HOW IT CONNECTS
    Tied to the `Task` model. `ApprovalEngine` will mutate these rows.
"""

import enum
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator, VARCHAR

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task


class ApprovalStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EDITED = "EDITED"
    RESUMED = "RESUMED"


# Custom JSON type fallback since we discovered SQLite doesn't natively support JSONB in this stack
class JSONVariant(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    
    # Track who is responsible for the decision
    approver_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(SAEnum(ApprovalStatus, name="approval_status_enum"), default=ApprovalStatus.PENDING_APPROVAL, index=True)
    
    # Original AI output vs Human Edited output
    original_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit trail
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    task: Mapped["Task"] = relationship("Task", backref="approvals")


class WorkflowCheckpoint(Base, TimestampMixin):
    """
    Persists LangGraph execution state.
    Instead of implementing the full complex LangGraph Checkpointer interface,
    we serialize the specific WorkflowState into JSON, allowing us to manually
    resume the ReAct loop dynamically by loading the graph with this state.
    """
    __tablename__ = "workflow_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), unique=True)
    
    # The serialized workflow state containing reasoning history, messages, and tool outputs
    state_json: Mapped[dict | list | None] = mapped_column(JSONVariant, nullable=True)
    
    # The last node that executed
    last_node: Mapped[str | None] = mapped_column(String(100), nullable=True)
