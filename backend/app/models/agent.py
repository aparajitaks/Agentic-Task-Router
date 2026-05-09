"""
app/models/agent.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Agents are the workers that process Tasks.  When the AI layer is added,
    each LangGraph/CrewAI agent will be registered here so the system knows
    what capabilities are available, which agents are active, and which tasks
    they own.

WHAT IT DOES
    - Stores agent metadata: name, type (e.g. "llm", "tool", "human")
    - Tracks `is_active` so we can disable agents without deleting their history
    - `max_concurrent_tasks` will be used by the future task-assignment algorithm

HOW IT CONNECTS
    app/models/task.py     → assigned_agent_id FK points here
    app/services/task.py   → validates assigned_agent_id exists before assigning
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, Integer, String
from sqlalchemy.types import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    # Imported only during type-checking to avoid the circular import:
    # agent.py → task.py → agent.py  (would fail at runtime)
    from app.models.task import Task


class AgentType(str, enum.Enum):
    """
    Classifies what kind of agent this represents.

    LLM     → AI language model agent (GPT-4, Gemini, Claude, etc.)
    TOOL    → Deterministic tool/script agent (web scraper, calculator)
    HUMAN   → Human-in-the-loop agent for review/approval steps
    ROUTER  → Meta-agent that delegates to other agents (LangGraph supervisor)
    """

    LLM = "llm"
    TOOL = "tool"
    HUMAN = "human"
    ROUTER = "router"


class Agent(Base, TimestampMixin):
    """
    Represents an agent that can be assigned to process Tasks.

    Table: agents
    """

    __tablename__ = "agents"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,            # Each agent must have a distinct name
        index=True,
        doc="Unique human-readable name (e.g. 'gmail-reader-agent').",
    )

    type: Mapped[AgentType] = mapped_column(
        SAEnum(
            AgentType,
            name="agent_type_enum",
            create_type=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AgentType.LLM,
        doc="Functional category of this agent.",
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        doc="Optional description of what this agent does.",
    )

    # ── Operational State ─────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Only active agents receive new task assignments.",
    )

    max_concurrent_tasks: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        doc="Maximum number of tasks this agent can process simultaneously.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    tasks: Mapped[list[Task]] = relationship(
        "Task",
        back_populates="assigned_agent",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id!s:.8} name={self.name!r} type={self.type.value!r} active={self.is_active}>"
