"""
app/execution_engine/engine.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Celery runs synchronously, but our LangGraph workflow (`ainvoke`) and database
    layer (`asyncpg`) are asynchronous. We need a clean wrapper to bridge this gap.

WHAT IT DOES
    - Provides a synchronous interface `SyncWorkflowEngine` for Celery.
    - Manages an isolated asyncio event loop to run async database and LLM calls.
    - Updates task statuses (PROCESSING, COMPLETED, FAILED, RETRYING).
    - Logs worker_id and timestamps.

HOW IT CONNECTS
    Called by `execute_agentic_workflow_task` in `app/workers/tasks.py`.
"""

import asyncio
from datetime import datetime, timezone
import uuid

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.models.log import Log, LogLevel
from app.graphs.main_graph import app_graph
from app.state.workflow_state import WorkflowState
from app.core.logging import get_logger

logger = get_logger(__name__)

class SyncWorkflowEngine:
    """Synchronous wrapper for executing async workflows in Celery."""
    
    def run_workflow(self, task_id_str: str, worker_id: str):
        """Creates a new event loop and runs the async engine."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._async_run_workflow(task_id_str, worker_id))
        finally:
            loop.close()

    async def _async_run_workflow(self, task_id_str: str, worker_id: str):
        task_id = uuid.UUID(task_id_str)
        
        async with AsyncSessionLocal() as db:
            # 1. Fetch Task
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"Task {task_id} not found in DB.")
                return

            # 2. Update status to PROCESSING
            task.status = TaskStatus.PROCESSING
            task.execution_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            task.worker_id = worker_id
            
            # Log transition
            db.add(Log(
                task_id=task.id,
                message=f"Worker {worker_id} started processing.",
                level=LogLevel.INFO,
                source="celery_worker"
            ))
            
            await db.commit()
            
            # 3. Initialize LangGraph State
            initial_state: WorkflowState = {
                "task_id": str(task.id),
                "input_text": task.input_text or "",
                "route": None,
                "selected_agent": None,
                "current_status": "Started by Worker",
                "intermediate_steps": [],
                "final_output": None,
                "error_message": None
            }

            try:
                # 4. Execute Workflow
                final_state = await app_graph.ainvoke(initial_state)
                
                # 5. Handle Success
                if final_state.get("error_message") or final_state.get("route") == "unknown":
                    task.status = TaskStatus.FAILED
                    task.failure_reason = final_state.get("error_message") or "Routing failed."
                    task.output_text = task.failure_reason
                    log_level = LogLevel.ERROR
                else:
                    task.status = TaskStatus.COMPLETED
                    task.output_text = final_state.get("final_output")
                    task.route_taken = final_state.get("route")
                    log_level = LogLevel.INFO
                    
                task.execution_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                
                db.add(Log(
                    task_id=task.id,
                    message=f"Workflow finished: {task.status.value}",
                    level=log_level,
                    source="celery_worker",
                    metadata_json={
                        "route": final_state.get("route"),
                        "error": final_state.get("error_message")
                    }
                ))
                
                await db.commit()
                
            except Exception as e:
                # Update retry count before re-raising for Celery to handle
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                db.add(Log(
                    task_id=task.id,
                    message=f"Execution error: {str(e)}. Triggering retry.",
                    level=LogLevel.ERROR,
                    source="celery_worker"
                ))
                await db.commit()
                raise e # Celery will catch this and retry
