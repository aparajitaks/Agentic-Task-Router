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
from app.models.task import TaskStatus
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import (
    create_task,
    get_all_tasks,
    get_task_by_id,
    soft_delete_task,
    update_task,
)

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
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await create_task(db, payload)
    return success_response(
        data=task.model_dump(mode="json"),
        message="Task created successfully.",
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    tasks, total = await get_all_tasks(db, page=page, page_size=page_size, status_filter=status_filter)
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await get_task_by_id(db, task_id)
    return success_response(
        data=task.model_dump(mode="json"),
        message="Task retrieved successfully.",
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await update_task(db, task_id, payload)
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    await soft_delete_task(db, task_id)
    return success_response(
        data={"task_id": str(task_id)},
        message="Task deleted successfully.",
    )
