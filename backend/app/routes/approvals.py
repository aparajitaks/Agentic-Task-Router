"""
app/routes/approvals.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This is the HTTP interface for the entire HITL system. Every action a
    human reviewer takes — approving, editing, rejecting — flows through
    these endpoints. The frontend polls GET /approvals for the live queue
    and fires POST requests when the human makes a decision.

WHAT IT DOES
    GET  /approvals              → Paginated list of all approvals (with filter)
    GET  /approvals/pending      → Live queue: only PENDING_APPROVAL records
    GET  /approvals/{id}         → Full detail for one approval (for the review UI)
    POST /approvals/{id}/approve → Human approves the AI draft as-is
    POST /approvals/{id}/edit    → Human corrects the draft and approves the edit
    POST /approvals/{id}/reject  → Human rejects the AI output entirely

HOW IT CONNECTS
    - app/services/approval.py  → All business logic delegated here
    - app/schemas/approval.py   → Request/response Pydantic models
    - app/core/responses.py     → Standard success_response/paginated_response wrappers
    - app/main.py               → Registered under /api/v1/approvals
"""

import uuid
from typing import Optional, cast

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.core.responses import success_response, paginated_response
from app.models.approval import ApprovalStatus
from app.schemas.approval import (
    ApprovalResponse,
    ApproveRequest,
    EditRequest,
    RejectRequest,
)
from app.services.approval import (
    get_approval_by_id,
    get_all_approvals,
    get_pending_approvals,
    process_approval_decision,
)

router = APIRouter(prefix="/approvals", tags=["Human-in-the-Loop Approvals"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List All Approvals",
    description=(
        "Returns a paginated audit log of all approval records. "
        "Use `status` filter to narrow to PENDING, APPROVED, REJECTED, etc."
    ),
)
async def list_approvals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ApprovalStatus] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    approvals, total = await get_all_approvals(
        db, user_id=cast(uuid.UUID, current_user.id), page=page, page_size=page_size, status_filter=status_filter
    )
    return paginated_response(
        data=[ApprovalResponse.model_validate(a).model_dump(mode="json") for a in approvals],
        total=total,
        page=page,
        page_size=page_size,
        message="Approvals retrieved successfully.",
    )


@router.get(
    "/pending",
    status_code=status.HTTP_200_OK,
    summary="Get Pending Approvals",
    description=(
        "Returns only PENDING_APPROVAL records. This is the primary endpoint "
        "the frontend polls to populate the live review queue."
    ),
)
async def list_pending_approvals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    approvals, total = await get_pending_approvals(db, user_id=cast(uuid.UUID, current_user.id), page=page, page_size=page_size)
    return paginated_response(
        data=[ApprovalResponse.model_validate(a).model_dump(mode="json") for a in approvals],
        total=total,
        page=page,
        page_size=page_size,
        message=f"{total} approvals awaiting human review.",
    )


@router.get(
    "/{approval_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Approval Detail",
    description=(
        "Returns the full detail of a single approval record including the "
        "AI draft, graph checkpoint context, and decision history."
    ),
)
async def get_approval(
    approval_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    approval = await get_approval_by_id(db, approval_id, cast(uuid.UUID, current_user.id))
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Approval retrieved.",
    )


@router.post(
    "/{approval_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve AI Output",
    description=(
        "Human approves the AI-generated draft as-is. "
        "This triggers immediate workflow resumption via Celery."
    ),
)
async def approve_workflow(
    approval_id: uuid.UUID,
    body: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    approval = await process_approval_decision(
        db,
        approval_id,
        cast(uuid.UUID, current_user.id),
        decision=ApprovalStatus.APPROVED,
        reviewer_id=body.reviewer_id,
        reviewer_name=body.reviewer_name,
    )
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Workflow approved and resumed successfully.",
    )


@router.post(
    "/{approval_id}/edit",
    status_code=status.HTTP_200_OK,
    summary="Edit and Approve AI Output",
    description=(
        "Human corrects the AI-generated draft and approves the edited version. "
        "The edit is recorded in full for compliance auditing. "
        "Workflow resumes using the human-corrected content."
    ),
)
async def edit_and_approve_workflow(
    approval_id: uuid.UUID,
    body: EditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    approval = await process_approval_decision(
        db,
        approval_id,
        cast(uuid.UUID, current_user.id),
        decision=ApprovalStatus.EDITED,
        reviewer_id=body.reviewer_id,
        reviewer_name=body.reviewer_name,
        human_edited_content=body.edited_content,
    )
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Edited content approved. Workflow resumed with your version.",
    )


@router.post(
    "/{approval_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject AI Output",
    description=(
        "Human rejects the AI-generated draft. "
        "A rejection reason is REQUIRED for compliance auditing. "
        "The associated task will be marked FAILED with the reason recorded."
    ),
)
async def reject_workflow(
    approval_id: uuid.UUID,
    body: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    approval = await process_approval_decision(
        db,
        approval_id,
        cast(uuid.UUID, current_user.id),
        decision=ApprovalStatus.REJECTED,
        reviewer_id=body.reviewer_id,
        reviewer_name=body.reviewer_name,
        rejection_reason=body.rejection_reason,
    )
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Workflow rejected. Task has been marked as failed.",
    )
