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
from typing import Optional, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.core.responses import success_response, paginated_response
from app.core.logging import get_logger
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

logger = get_logger(__name__)

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
) -> Any:
    approvals, total = await get_all_approvals(
        db, user_id=current_user.id, page=page, page_size=page_size, status_filter=status_filter
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
    summary="List Pending Approvals",
    description="Returns the active review queue for the human-in-the-loop dashboard.",
)
async def list_pending_approvals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    approvals, total = await get_pending_approvals(db, user_id=current_user.id, page=page, page_size=page_size)
    return paginated_response(
        data=[ApprovalResponse.model_validate(a).model_dump(mode="json") for a in approvals],
        total=total,
        page=page,
        page_size=page_size,
        message="Pending approvals retrieved.",
    )


@router.get(
    "/{approval_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Approval Detail",
    description="Returns the full detail of a specific approval record, including AI draft and context.",
)
async def get_approval(
    approval_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    approval = await get_approval_by_id(db, approval_id, current_user.id)
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Approval detail retrieved.",
    )


@router.post(
    "/{approval_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve AI Output",
    description="Human approves the AI-generated draft as-is. Triggers workflow resumption.",
)
async def approve_workflow(
    approval_id: uuid.UUID,
    body: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    approval = await process_approval_decision(
        db,
        approval_id,
        current_user.id,
        decision=ApprovalStatus.APPROVED,
        reviewer_id=body.reviewer_id,
        reviewer_name=body.reviewer_name,
    )
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Workflow approved and resumed.",
    )


@router.post(
    "/{approval_id}/edit",
    status_code=status.HTTP_200_OK,
    summary="Edit and Approve AI Output",
    description="Human corrects the AI-generated draft. Triggers workflow resumption with edited content.",
)
async def edit_and_approve_workflow(
    approval_id: uuid.UUID,
    body: EditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    approval = await process_approval_decision(
        db,
        approval_id,
        current_user.id,
        decision=ApprovalStatus.EDITED,
        reviewer_id=body.reviewer_id,
        reviewer_name=body.reviewer_name,
        human_edited_content=body.edited_content,
    )
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Workflow edited and resumed.",
    )


@router.post(
    "/{approval_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject AI Output",
    description="Human rejects the AI output. Workflow is terminated.",
)
async def reject_workflow(
    approval_id: uuid.UUID,
    body: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    approval = await process_approval_decision(
        db,
        approval_id,
        current_user.id,
        decision=ApprovalStatus.REJECTED,
        reviewer_id=body.reviewer_id,
        reviewer_name=body.reviewer_name,
        rejection_reason=body.rejection_reason,
    )
    return success_response(
        data=ApprovalResponse.model_validate(approval).model_dump(mode="json"),
        message="Workflow rejected and terminated.",
    )
