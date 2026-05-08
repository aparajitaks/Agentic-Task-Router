"""
app/models/tool.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Tools execute external actions (sending emails, deleting files, etc.). We MUST
    have a clear audit trail of every tool an AI agent used, what arguments it
    passed, and whether it succeeded or failed.

WHAT IT DOES
    - Defines `ToolExecutionLog`.
    - Tracks tool name, arguments (JSON), result (JSON/Text), duration, and status.

HOW IT CONNECTS
    The `ToolExecutionNode` in LangGraph will write to this table every time a
    tool finishes executing.
"""

import uuid
from sqlalchemy import String, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin

class ToolExecutionLog(Base, TimestampMixin):
    """Audit log for AI agent tool invocations."""
    __tablename__ = "tool_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=True)
    
    tool_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    arguments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    is_success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
