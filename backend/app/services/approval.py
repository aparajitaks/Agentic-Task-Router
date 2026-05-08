"""
app/services/approval.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The service layer is the boundary between the HTTP API (routes) and the
    database (models). All approval business logic lives here — not in routes,
    not in models. This separation makes everything testable and reusable.

WHAT IT DOES
    - `create_approval`: Called by the LangGraph HITL node to pause a workflow
      and persist a checkpoint for future resumption.
    - `get_approval_by_id`: Fetches a single approval with 404 handling.
    - `get_pending_approvals`: Returns the review queue for the dashboard.
    - `process_approval_decision`: Core logic — validates the decision, records
      the human action, updates the task status, and enqueues workflow resumption.
    - `expire_stale_approvals`: Background job function that marks approvals
      past their SLA deadline as EXPIRED.

HOW IT CONNECTS
    - app/routes/approvals.py  → Calls service functions from HTTP handlers
    - app/graphs/main_graph.py → Calls `create_approval` when pausing
    - app/workers/resume.py    → Triggered by `process_approval_decision` to
                                  resume graph execution
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval, ApprovalStatus
from app.models.task import Task, TaskStatus
from app.core.logging import get_logger
from app.core.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

# Default SLA: human must decide within 24 hours before auto-expiry
DEFAULT_APPROVAL_SLA_HOURS = 24


async def create_approval(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    ai_generated_draft: str,
    original_input: str,
    graph_checkpoint_state: dict,
    checkpoint_node: str,
    workflow_context: Optional[dict] = None,
    sla_hours: int = DEFAULT_APPROVAL_SLA_HOURS,
) -> Approval:
    """
    Creates a new approval checkpoint and pauses the associated task.

    Called atomically from the LangGraph HITL node. After this call:
    - The Task status is AWAITING_APPROVAL
    - The graph state is persisted in `graph_checkpoint_state`
    - The frontend can display the approval in the review queue

    Returns the created Approval record.
    """
    # 1. Create the approval record
    approval = Approval(
        task_id=task_id,
        ai_generated_draft=ai_generated_draft,
        original_input=original_input,
        graph_checkpoint_state=graph_checkpoint_state,
        checkpoint_node=checkpoint_node,
        workflow_context=workflow_context or {},
        status=ApprovalStatus.PENDING_APPROVAL,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=sla_hours),
    )
    db.add(approval)

    # 2. Pause the task — transition to AWAITING_APPROVAL
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task:
        task.status = TaskStatus.AWAITING_APPROVAL

    await db.commit()
    await db.refresh(approval)

    logger.info(
        "Approval checkpoint created | approval_id=%s task_id=%s expires_at=%s",
        approval.id, task_id, approval.expires_at
    )
    return approval


async def get_approval_by_id(db: AsyncSession, approval_id: uuid.UUID) -> Approval:
    """
    Fetches an Approval by its UUID. Raises NotFoundError if absent.
    """
    stmt = select(Approval).where(Approval.id == approval_id)
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()
    if not approval:
        raise NotFoundError(f"Approval {approval_id} not found.")
    return approval


async def get_pending_approvals(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Approval], int]:
    """
    Returns the human review queue — all PENDING_APPROVAL records, newest first.
    Used to populate the approval inbox on the frontend dashboard.
    """
    offset = (page - 1) * page_size

    count_stmt = (
        select(func.count())
        .select_from(Approval)
        .where(Approval.status == ApprovalStatus.PENDING_APPROVAL)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(Approval)
        .where(Approval.status == ApprovalStatus.PENDING_APPROVAL)
        .order_by(Approval.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    approvals = list(result.scalars().all())

    return approvals, total


async def get_all_approvals(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[ApprovalStatus] = None,
) -> tuple[list[Approval], int]:
    """
    Returns all approval records for the audit dashboard with optional status filtering.
    """
    offset = (page - 1) * page_size

    where_clause = []
    if status_filter:
        where_clause.append(Approval.status == status_filter)

    count_stmt = select(func.count()).select_from(Approval)
    if where_clause:
        count_stmt = count_stmt.where(*where_clause)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = select(Approval).order_by(Approval.created_at.desc()).offset(offset).limit(page_size)
    if where_clause:
        stmt = stmt.where(*where_clause)
    result = await db.execute(stmt)
    approvals = list(result.scalars().all())

    return approvals, total


async def process_approval_decision(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    decision: ApprovalStatus,  # APPROVED | EDITED | REJECTED
    reviewer_id: str = "system",
    reviewer_name: str = "Unknown Reviewer",
    human_edited_content: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> Approval:
    """
    Core HITL decision handler. This is the most critical function in the system.

    Validates the transition, records the human decision with full audit metadata,
    and triggers workflow resumption via Celery (or marks the task FAILED on reject).

    Decision Rules:
    - APPROVED: Resume workflow with the original AI-generated draft.
    - EDITED: Resume workflow using the human's corrected content.
    - REJECTED: Mark task as FAILED, record the reason. No resumption.
    """
    approval = await get_approval_by_id(db, approval_id)

    # Guard: Cannot act on a decision already made
    if approval.status != ApprovalStatus.PENDING_APPROVAL:
        raise ValidationError(
            f"Approval {approval_id} has already been decided (status={approval.status.value}). "
            f"Cannot re-process a closed approval."
        )

    # Guard: EDITED requires content
    if decision == ApprovalStatus.EDITED and not human_edited_content:
        raise ValidationError(
            "An edited approval must include `human_edited_content`."
        )

    # Guard: REJECTED requires a reason (enterprise audit requirement)
    if decision == ApprovalStatus.REJECTED and not rejection_reason:
        raise ValidationError(
            "A rejected approval must include a `rejection_reason` for audit purposes."
        )

    now = datetime.now(timezone.utc)

    # Record the decision
    approval.status = decision
    approval.decided_at = now
    approval.reviewer_id = reviewer_id
    approval.reviewer_name = reviewer_name
    approval.human_edited_content = human_edited_content
    approval.rejection_reason = rejection_reason

    # Determine the final content to resume with
    final_content = human_edited_content if decision == ApprovalStatus.EDITED else approval.ai_generated_draft

    # Update task status based on decision
    stmt = select(Task).where(Task.id == approval.task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if decision == ApprovalStatus.REJECTED:
        if task:
            task.status = TaskStatus.FAILED
            task.failure_reason = f"Rejected by {reviewer_name}: {rejection_reason}"
        await db.commit()
        await db.refresh(approval)
        logger.info(
            "Approval REJECTED | approval_id=%s task_id=%s reviewer=%s reason=%s",
            approval_id, approval.task_id, reviewer_name, rejection_reason,
        )
        return approval

    # For APPROVED / EDITED: enqueue workflow resumption
    # Import here to avoid circular imports at module load time
    from app.workers.resume import resume_workflow_task

    checkpoint = approval.graph_checkpoint_state or {}
    # Inject the final (possibly human-edited) content into the checkpoint
    checkpoint["final_output"] = final_content
    checkpoint["hitl_decision"] = decision.value
    checkpoint["hitl_reviewer"] = reviewer_name

    if task:
        task.status = TaskStatus.PROCESSING  # Back to processing while resuming

    await db.commit()
    await db.refresh(approval)

    # Enqueue the Celery task to resume graph execution
    celery_result = resume_workflow_task.delay(
        str(approval.task_id),
        str(approval.id),
        checkpoint,
    )

    # Update the approval with the Celery resume task ID for traceability
    approval.resume_task_id = celery_result.id
    approval.resumed_at = now
    await db.commit()
    await db.refresh(approval)

    logger.info(
        "Approval %s | resuming task=%s via celery_task=%s | reviewer=%s",
        decision.value.upper(), approval.task_id, celery_result.id, reviewer_name,
    )
    return approval


async def expire_stale_approvals(db: AsyncSession) -> int:
    """
    Marks all PENDING_APPROVAL records past their SLA deadline as EXPIRED.

    Should be called by a periodic Celery beat task (e.g., every hour).
    Returns the count of expired records for observability metrics.
    """
    now = datetime.now(timezone.utc)

    stmt = (
        select(Approval)
        .where(
            Approval.status == ApprovalStatus.PENDING_APPROVAL,
            Approval.expires_at < now,
        )
    )
    result = await db.execute(stmt)
    stale = list(result.scalars().all())

    for approval in stale:
        approval.status = ApprovalStatus.EXPIRED
        # Also fail the associated task
        task_stmt = select(Task).where(Task.id == approval.task_id)
        task_result = await db.execute(task_stmt)
        task = task_result.scalar_one_or_none()
        if task and task.status == TaskStatus.AWAITING_APPROVAL:
            task.status = TaskStatus.FAILED
            task.failure_reason = f"Approval expired without human decision (SLA breached at {now.isoformat()})"

    if stale:
        await db.commit()
        logger.warning("Expired %d stale approvals past SLA deadline.", len(stale))

    return len(stale)
