"""
app/routes/tasks.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Routes are the HTTP adapters — their ONLY job is:
      1. Parse and validate the request (Pydantic does this automatically)
      2. Delegate work to the service layer
      3. Wrap the result in a consistent API envelope
      4. Return the correct HTTP status code

WHAT IT DOES
    Implements the full CRUD surface for Tasks:
      POST   /api/v1/tasks            → Create Task
      GET    /api/v1/tasks            → List Tasks (paginated, filterable)
      GET    /api/v1/tasks/{task_id}  → Get Single Task
      PATCH  /api/v1/tasks/{task_id}  → Partial Update Task
      DELETE /api/v1/tasks/{task_id}  → Soft-Delete Task
"""

from __future__ import annotations
import uuid
from typing import Optional, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.core.responses import paginated_response, success_response
from app.db.session import get_db
from app.models.task import TaskStatus, Task
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskExecuteRequest
from app.workers.tasks import execute_agentic_workflow_task
from app.services import (
    create_task,
    get_all_tasks,
    get_task_by_id,
    soft_delete_task,
    update_task,
)
from app.models.log import Log

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Task",
)
async def create_task_route(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    task = await create_task(db, payload, current_user.id)
    return success_response(
        data=TaskResponse.model_validate(task).model_dump(mode="json"),
        message="Task created successfully.",
    )


@router.post(
    "/execute",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute an AI Workflow",
)
async def execute_workflow_route(
    payload: TaskExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    try:
        # 1. Create task in DB as QUEUED
        task = Task(
            title=payload.title,
            description="Async AI Workflow Execution",
            input_text=payload.input_text,
            status=TaskStatus.QUEUED,
            user_id=current_user.id
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # 2. Push to Celery/Redis queue
        execute_agentic_workflow_task.delay(str(task.id))
        
        return success_response(
            data=TaskResponse.model_validate(task).model_dump(mode="json"),
            message="Workflow successfully queued for processing.",
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Failed to queue workflow: %s", str(e))
        from app.core.exceptions import ValidationException
        raise ValidationException("Task creation failed: Could not queue the workflow.")


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List Tasks",
)
async def list_tasks_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    tasks, total = await get_all_tasks(db, user_id=current_user.id, page=page, page_size=page_size, status_filter=status_filter)
    return paginated_response(
        data=[TaskResponse.model_validate(t).model_dump(mode="json") for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        message="Tasks retrieved successfully.",
    )


@router.get(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a Task by ID",
)
async def get_task_route(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    task = await get_task_by_id(db, task_id, current_user.id)
    return success_response(
        data=TaskResponse.model_validate(task).model_dump(mode="json"),
        message="Task retrieved successfully.",
    )


@router.get(
    "/{task_id}/logs",
    status_code=status.HTTP_200_OK,
    summary="Get Task Execution Logs",
)
async def get_task_logs_route(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Verify task ownership
    await get_task_by_id(db, task_id, current_user.id)
    
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


@router.patch(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Partially update a Task",
)
async def update_task_route(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    task = await update_task(db, task_id, current_user.id, payload)
    return success_response(
        data=TaskResponse.model_validate(task).model_dump(mode="json"),
        message="Task updated successfully.",
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a Task",
)
async def delete_task_route(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await soft_delete_task(db, task_id, current_user.id)
    return success_response(
        data={"task_id": str(task_id)},
        message="Task deleted successfully.",
    )
