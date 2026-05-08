"""
app/schemas/approval.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Pydantic schemas decouple the HTTP API shape from the SQLAlchemy ORM model.
    This is critical because:
    - Request bodies must be validated and typed before touching the database
    - Response bodies must be carefully controlled (never leak internal fields)
    - The approval lifecycle has distinct schemas for each operation

WHAT IT DOES
    Defines typed Pydantic v2 schemas for:
    - ApprovalResponse: What the API returns for any approval record
    - ApprovalDecisionRequest: The request body for approve/reject/edit
    - ApprovalListResponse: Paginated list of approvals

HOW IT CONNECTS
    - app/routes/approvals.py  → Uses these schemas for validation and serialization
    - app/services/approval.py → Returns ORM objects that are converted here
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.approval import ApprovalStatus


class ApprovalResponse(BaseModel):
    """
    Full representation of an Approval record returned by the API.
    Includes all fields needed by the frontend review UI.
    """
    id: uuid.UUID
    task_id: uuid.UUID
    status: ApprovalStatus

    ai_generated_draft: Optional[str] = None
    original_input: Optional[str] = None
    workflow_context: Optional[dict[str, Any]] = None
    checkpoint_node: Optional[str] = None

    human_edited_content: Optional[str] = None
    rejection_reason: Optional[str] = None

    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None

    decided_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    resume_task_id: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    """Request body for POST /approvals/{id}/approve"""
    reviewer_id: str = Field(default="anonymous", description="Identifier of the reviewing user.")
    reviewer_name: str = Field(default="Human Reviewer", description="Display name for audit logs.")


class EditRequest(BaseModel):
    """Request body for POST /approvals/{id}/edit"""
    edited_content: str = Field(
        ...,
        min_length=1,
        description="The human-corrected version of the AI-generated content.",
    )
    reviewer_id: str = Field(default="anonymous")
    reviewer_name: str = Field(default="Human Reviewer")


class RejectRequest(BaseModel):
    """Request body for POST /approvals/{id}/reject"""
    rejection_reason: str = Field(
        ...,
        min_length=10,
        description="Required explanation of why the AI output was rejected. Stored for audit.",
    )
    reviewer_id: str = Field(default="anonymous")
    reviewer_name: str = Field(default="Human Reviewer")


class ApprovalListResponse(BaseModel):
    """Paginated response for GET /approvals"""
    data: list[ApprovalResponse]
    total: int
    page: int
    page_size: int
    pending_count: int = Field(description="Total number of approvals still awaiting decision.")
