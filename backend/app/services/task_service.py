"""
app/services/task_service.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Routes should be thin HTTP adapters — they validate input, call services,
    and return responses.  All business logic lives here in the service layer:
      - Database queries
      - Business rules (e.g. "you can't COMPLETE a CANCELLED task")
      - Raising domain exceptions (NotFoundException, etc.)
      - Creating audit log entries

    This separation means you can:
      - Unit-test business logic without starting a FastAPI server
      - Reuse service functions from Celery workers, CLI scripts, or other routes
      - Swap the database without touching routes

WHAT IT DOES
    Implements all CRUD operations for Tasks:
      create_task()         — validate + insert + create log entry
      get_all_tasks()       — paginated list with soft-delete filter
      get_task_by_id()      — single task or raise NotFoundException
      update_task()         — partial update with field-level control
      soft_delete_task()    — mark is_deleted=True, never hard-delete

HOW IT CONNECTS
    app/routes/tasks.py       → calls every function here
    app/db/session.py         → receives AsyncSession as a parameter
    app/models/task.py        → Task ORM model manipulated here
    app/models/log.py         → Log entries created here for audit trail
    app/core/exceptions.py    → raises NotFoundException / ValidationException
    app/schemas/task.py       → TaskCreate / TaskUpdate consumed here
"""

from __future__ import annotations

import uuid
from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import get_logger
from app.models.agent import Agent
from app.models.log import Log, LogLevel
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _create_log(
    db: AsyncSession,
    task_id: uuid.UUID,
    message: str,
    level: LogLevel = LogLevel.INFO,
    source: str = "api",
    metadata: dict | None = None,
) -> None:
    """Create an immutable audit log entry for a Task event."""
    log = Log(
        task_id=task_id,
        message=message,
        level=level,
        source=source,
        metadata_json=metadata,
    )
    db.add(log)
    # Log is flushed as part of the same transaction as the Task change


async def _get_task_or_404(db: AsyncSession, task_id: uuid.UUID) -> Task:
    """Fetch a non-deleted Task by ID, or raise NotFoundException."""
    stmt = select(Task).where(Task.id == task_id, Task.is_deleted.is_(False))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundException("Task", task_id)
    return task


# ─────────────────────────────────────────────────────────────────────────────
# Status Transition Validation
# ─────────────────────────────────────────────────────────────────────────────

# Legal state transitions: current_status → set of allowed next statuses
_ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING:      {TaskStatus.QUEUED, TaskStatus.CANCELLED},
    TaskStatus.QUEUED:       {TaskStatus.PROCESSING, TaskStatus.CANCELLED},
    TaskStatus.PROCESSING:   {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.RETRYING, TaskStatus.CANCELLED},
    TaskStatus.RETRYING:     {TaskStatus.QUEUED, TaskStatus.PROCESSING, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED:    set(),                 # Terminal state
    TaskStatus.FAILED:       {TaskStatus.QUEUED, TaskStatus.PENDING},  # Allow manual/auto retry
    TaskStatus.CANCELLED:    set(),                 # Terminal state
}


def _validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """
    Enforce state machine rules.

    Raises ValidationException if the transition is not permitted.
    """
    if new == current:
        return   # Same status is always a no-op, not an error
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValidationException(
            message=(
                f"Cannot transition task from '{current.value}' to '{new.value}'. "
                f"Allowed transitions: {[s.value for s in allowed] or 'none (terminal state)'}."
            )
        )


# ─────────────────────────────────────────────────────────────────────────────
# Public Service Functions
# ─────────────────────────────────────────────────────────────────────────────

async def create_task(db: AsyncSession, payload: TaskCreate) -> TaskResponse:
    """
    Create a new Task and insert the first audit log entry.

    Args:
        db:      Async database session (injected via Depends).
        payload: Validated TaskCreate schema from the request body.

    Returns:
        TaskResponse Pydantic model representing the newly created task.
    """
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    db.add(task)
    await db.flush()   # Flush to get the DB-generated `id` before creating the log

    await _create_log(
        db=db,
        task_id=task.id,
        message=f"Task '{task.title}' created with status '{task.status.value}'.",
        level=LogLevel.INFO,
        source="api",
    )

    logger.info("Task created | id=%s title=%r", task.id, task.title)
    return TaskResponse.model_validate(task)


async def get_all_tasks(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: TaskStatus | None = None,
) -> Tuple[List[TaskResponse], int]:
    """
    Return a paginated list of non-deleted Tasks.

    Args:
        db:            Async DB session.
        page:          1-indexed page number.
        page_size:     Number of items per page (max 100).
        status_filter: Optional filter by TaskStatus enum value.

    Returns:
        Tuple of (list of TaskResponse, total_count).
        Callers use total_count to build pagination metadata.
    """
    page_size = min(page_size, 100)  # Hard cap to prevent abuse
    offset = (page - 1) * page_size

    # Base query — always exclude soft-deleted tasks
    base_filter = [Task.is_deleted.is_(False)]
    if status_filter:
        base_filter.append(Task.status == status_filter)

    # Total count query (no offset/limit)
    count_stmt = select(func.count()).select_from(Task).where(*base_filter)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Data query with pagination
    stmt = (
        select(Task)
        .where(*base_filter)
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return [TaskResponse.model_validate(t) for t in tasks], total


async def get_task_by_id(db: AsyncSession, task_id: uuid.UUID) -> TaskResponse:
    """
    Return a single Task by its UUID, or raise NotFoundException.

    Args:
        db:      Async DB session.
        task_id: UUID of the task to retrieve.

    Returns:
        TaskResponse Pydantic model.

    Raises:
        NotFoundException: If no non-deleted task exists with this ID.
    """
    task = await _get_task_or_404(db, task_id)
    return TaskResponse.model_validate(task)


async def update_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    payload: TaskUpdate,
) -> TaskResponse:
    """
    Partially update a Task.  Only provided fields are changed.

    Enforces state-machine rules if `status` is being changed.
    Validates that `assigned_agent_id` refers to an existing active Agent.

    Args:
        db:      Async DB session.
        task_id: UUID of the task to update.
        payload: TaskUpdate schema with optional fields.

    Returns:
        Updated TaskResponse.

    Raises:
        NotFoundException:   Task not found / Agent not found.
        ValidationException: Invalid status transition.
    """
    task = await _get_task_or_404(db, task_id)
    changes: list[str] = []

    # ── Status transition ─────────────────────────────────────────────────────
    if payload.status is not None and payload.status != task.status:
        _validate_status_transition(task.status, payload.status)
        old_status = task.status.value
        task.status = payload.status
        changes.append(f"status: {old_status} → {payload.status.value}")

    # ── Title update ──────────────────────────────────────────────────────────
    if payload.title is not None and payload.title != task.title:
        changes.append(f"title: '{task.title}' → '{payload.title}'")
        task.title = payload.title

    # ── Description update ────────────────────────────────────────────────────
    if payload.description is not None:
        task.description = payload.description
        changes.append("description updated")

    # ── Agent assignment ──────────────────────────────────────────────────────
    if payload.assigned_agent_id is not None:
        # Verify the agent exists and is active
        agent_stmt = select(Agent).where(
            Agent.id == payload.assigned_agent_id,
            Agent.is_active.is_(True),
        )
        agent_result = await db.execute(agent_stmt)
        agent = agent_result.scalar_one_or_none()
        if agent is None:
            raise NotFoundException("Active Agent", payload.assigned_agent_id)
        task.assigned_agent_id = payload.assigned_agent_id
        changes.append(f"assigned_agent_id → {payload.assigned_agent_id}")

    # ── Audit log ──────────────────────────────────────────────────────────────
    if changes:
        await _create_log(
            db=db,
            task_id=task.id,
            message=f"Task updated: {'; '.join(changes)}.",
            level=LogLevel.INFO,
            source="api",
            metadata={"changes": changes},
        )
        logger.info("Task updated | id=%s changes=%s", task.id, changes)
    else:
        logger.debug("Task update called with no actual changes | id=%s", task.id)

    await db.flush()
    return TaskResponse.model_validate(task)


async def soft_delete_task(db: AsyncSession, task_id: uuid.UUID) -> None:
    """
    Soft-delete a Task by setting is_deleted=True.

    WHY soft-delete? Tasks may have Log entries referencing them.
    Hard-deleting would violate audit requirements and break foreign keys.

    Args:
        db:      Async DB session.
        task_id: UUID of the task to delete.

    Raises:
        NotFoundException: Task not found.
    """
    task = await _get_task_or_404(db, task_id)
    task.is_deleted = True

    await _create_log(
        db=db,
        task_id=task.id,
        message=f"Task '{task.title}' soft-deleted.",
        level=LogLevel.WARNING,
        source="api",
    )

    logger.warning("Task soft-deleted | id=%s title=%r", task.id, task.title)
    await db.flush()
