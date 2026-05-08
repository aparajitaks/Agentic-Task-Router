"""
app/routes/tasks.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Routes are the HTTP adapters — their ONLY job is:
      1. Parse and validate the request (Pydantic does this automatically)
      2. Delegate work to the service layer
      3. Wrap the result in a consistent API envelope
      4. Return the correct HTTP status code

    No business logic belongs here.  If a route is longer than ~20 lines,
    something is wrong.

WHAT IT DOES
    Implements the full CRUD surface for Tasks:
      POST   /api/v1/tasks            → Create Task
      GET    /api/v1/tasks            → List Tasks (paginated, filterable)
      GET    /api/v1/tasks/{task_id}  → Get Single Task
      PATCH  /api/v1/tasks/{task_id}  → Partial Update Task
      DELETE /api/v1/tasks/{task_id}  → Soft-Delete Task

HOW IT CONNECTS
    app/main.py             → router registered under /api/v1 prefix
    app/services/task.py    → all route handlers delegate here
    app/db/session.py       → get_db injected via Depends()
    app/core/responses.py   → success_response / paginated_response used here
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.responses import paginated_response, success_response
from app.db.session import get_db
from app.models.task import TaskStatus, Task
from app.core.auth import get_current_user
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskExecuteRequest
from app.services import (
    create_task,
    get_all_tasks,
    get_task_by_id,
    soft_delete_task,
    update_task,
)
from app.models.log import Log
from sqlalchemy import select
from app.models.task import Task
from app.core.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/tasks — Create Task
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=None,          # We return a dict envelope, not a bare Pydantic model
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Task",
    description=(
        "Creates a new Task in PENDING state.  "
        "The task is immediately available for agent assignment."
    ),
)
async def create_task_route(
    payload: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await create_task(db, payload, user.id)
    return success_response(
        data=task.model_dump(mode="json"),
        message="Task created successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/tasks/execute — Execute AI Workflow
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/execute",
    response_model=None,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute an AI Workflow",
    description="Creates a task and queues it for asynchronous LangGraph execution.",
)
async def execute_workflow_route(
    payload: TaskExecuteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # 1. Create task in DB as QUEUED
    task = Task(
        title=payload.title,
        description="Async AI Workflow Execution",
        input_text=payload.input_text,
        status=TaskStatus.QUEUED,
        user_id=user.id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 2. Push to Celery/Redis queue
    execute_agentic_workflow_task.delay(str(task.id))
    
    response_data = TaskResponse.model_validate(task).model_dump(mode="json")
    
    return success_response(
        data=response_data,
        message="Workflow successfully queued for processing.",
    )



# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/tasks — List All Tasks
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="List Tasks",
    description="Returns a paginated list of tasks with optional status filtering.",
)
async def list_tasks_route(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    status_filter: Optional[TaskStatus] = Query(
        default=None,
        alias="status",
        description="Filter tasks by lifecycle status.",
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    tasks, total = await get_all_tasks(db, user_id=user.id, page=page, page_size=page_size, status_filter=status_filter)
    return paginated_response(
        data=[t.model_dump(mode="json") for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        message="Tasks retrieved successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/tasks/{task_id} — Get Single Task
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{task_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Get a Task by ID",
)
async def get_task_route(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await get_task_by_id(db, task_id, user.id)
    return success_response(
        data=task.model_dump(mode="json"),
        message="Task retrieved successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/tasks/{task_id}/workflow — Get Workflow State
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{task_id}/workflow",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Get Task Workflow State",
    description="Returns the task including its AI input, output, and routing details.",
)
async def get_task_workflow_route(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await get_task_by_id(db, task_id, user.id)
    return success_response(
        data=task.model_dump(mode="json"),
        message="Workflow state retrieved.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/tasks/{task_id}/logs — Get Execution Logs
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{task_id}/logs",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Get Task Execution Logs",
    description="Returns the immutable audit trail for a specific task.",
)
async def get_task_logs_route(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # First verify task ownership
    await get_task_by_id(db, task_id, user.id)
    
    # Basic query to fetch logs ordered by timestamp
    query = select(Log).where(Log.task_id == task_id).order_by(Log.timestamp.asc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    logs_data = [
        {
            "id": str(log.id),
            "message": log.message,
            "level": log.level.value,
            "source": log.source,
            "metadata": log.metadata_json,
            "timestamp": log.timestamp.isoformat() + "Z"
        }
        for log in logs
    ]
    
    return success_response(
        data={"logs": logs_data},
        message="Logs retrieved successfully.",
    )



# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/tasks/{task_id} — Partial Update
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{task_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Partially update a Task",
    description="Update any combination of title, description, status, or assigned agent.",
)
async def update_task_route(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await update_task(db, task_id, user.id, payload)
    return success_response(
        data=task.model_dump(mode="json"),
        message="Task updated successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/v1/tasks/{task_id} — Soft Delete
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/{task_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a Task",
    description=(
        "Marks the task as deleted (is_deleted=True) without removing it from the DB.  "
        "This preserves the audit log history."
    ),
)
async def delete_task_route(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await soft_delete_task(db, task_id, user.id)
    return success_response(
        data={"task_id": str(task_id)},
        message="Task deleted successfully.",
    )
