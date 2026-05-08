"""
app/schemas/task.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    SQLAlchemy models define how data is stored; Pydantic schemas define what
    the API accepts and returns.  Keeping them separate means:
      - DB column changes don't accidentally expose internal fields to the API
      - API contracts can evolve independently from the DB schema
      - Validation logic lives here, not scattered across routes

WHAT IT DOES
    Defines four Pydantic v2 schemas:
      TaskCreate       → fields required to create a new task (POST body)
      TaskUpdate       → all fields optional for partial update (PATCH body)
      TaskResponse     → what the API returns (includes DB-generated fields)
      TaskListResponse → wraps a list for paginated responses

HOW IT CONNECTS
    app/routes/tasks.py  → uses these as route request/response type hints
    app/services/task.py → receives TaskCreate/TaskUpdate, returns TaskResponse
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.models.task import TaskStatus


# ─────────────────────────────────────────────────────────────────────────────
# Request Schemas (what the API accepts)
# ─────────────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """
    Schema for creating a new Task via POST /api/v1/tasks.

    Validation rules:
    - title is required and must be 1-255 characters
    - description is optional but capped at 5000 characters
    - status defaults to PENDING (client should not control initial state)
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Analyse Q1 sales emails"],
        description="Short human-readable title for the task.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        examples=["Read all emails labelled Q1-Sales and extract revenue mentions."],
        description="Optional detailed description of the work to be done.",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Initial lifecycle status (defaults to PENDING).",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank or whitespace-only.")
        return stripped


class TaskUpdate(BaseModel):
    """
    Schema for partially updating a Task via PATCH /api/v1/tasks/{id}.

    All fields are Optional — send only the fields you want to change.
    This follows the PATCH semantics (partial update, not full replace).
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated title.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Updated description.",
    )
    status: Optional[TaskStatus] = Field(
        default=None,
        description="Updated lifecycle status.",
    )
    assigned_agent_id: Optional[uuid.UUID] = Field(
        default=None,
        description="UUID of the agent to assign this task to.",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("title must not be blank or whitespace-only.")
            return stripped
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Response Schemas (what the API returns)
# ─────────────────────────────────────────────────────────────────────────────

class TaskExecuteRequest(BaseModel):
    """
    Schema for executing a task via POST /api/v1/tasks/execute.
    """
    input_text: str = Field(
        ...,
        min_length=1,
        examples=["Summarize this email about Q1 sales..."],
        description="Raw input text to be routed and processed.",
    )
    title: str = Field(
        default="Auto-generated Task",
        description="Optional title for the task record.",
    )


class TaskResponse(BaseModel):
    """
    Schema for a single Task returned by the API.

    Uses `model_config = ConfigDict(from_attributes=True)` (Pydantic v2) to
    allow constructing this schema directly from a SQLAlchemy ORM instance
    via `TaskResponse.model_validate(task_orm_object)`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    input_text: Optional[str]
    output_text: Optional[str]
    route_taken: Optional[str]
    status: TaskStatus
    assigned_agent_id: Optional[uuid.UUID]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("id", "assigned_agent_id")
    def serialize_uuid(self, value: Optional[uuid.UUID]) -> Optional[str]:
        """Serialise UUID fields as plain strings in JSON responses."""
        return str(value) if value is not None else None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialise datetime fields as ISO-8601 strings with UTC 'Z' suffix."""
        return value.isoformat() + "Z"


