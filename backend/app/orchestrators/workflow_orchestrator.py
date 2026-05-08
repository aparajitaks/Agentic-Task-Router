"""
app/orchestrators/workflow_orchestrator.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The Orchestrator acts as the bridge between our FastAPI HTTP routes and
    the LangGraph AI system. It handles database transactions, logging, and
    error catching so the AI graph doesn't have to worry about infrastructure.

WHAT IT DOES
    - Takes an incoming request.
    - Creates a Task record in PostgreSQL.
    - Initializes the WorkflowState.
    - Invokes the LangGraph workflow.
    - Updates the Task record with the final output and route.
    - Writes an immutable Log entry for audit purposes.

HOW IT CONNECTS
    Called by `POST /api/v1/tasks/execute` in `app/routes/tasks.py`.
"""

import json
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.task import Task, TaskStatus
from app.models.log import Log, LogLevel
from app.schemas.task import TaskExecuteRequest
from app.graphs.main_graph import app_graph
from app.state.workflow_state import WorkflowState


class WorkflowOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_task(self, request: TaskExecuteRequest) -> Task:
        """
        Executes the full agentic workflow for a given input.
        """
        # 1. Create the initial Task in the database
        task = Task(
            title=request.title,
            description="AI Workflow Execution",
            input_text=request.input_text,
            status=TaskStatus.IN_PROGRESS
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # 2. Initialize the LangGraph State
        initial_state: WorkflowState = {
            "task_id": str(task.id),
            "input_text": request.input_text,
            "route": None,
            "selected_agent": None,
            "current_status": "Started",
            "intermediate_steps": [],
            "final_output": None,
            "error_message": None
        }

        # 3. Execute the Graph
        # We run this synchronously for now, but LangGraph supports async (ainvoke)
        # We'll use ainvoke so it doesn't block the FastAPI event loop.
        final_state = await app_graph.ainvoke(initial_state)

        # 4. Process the Results
        if final_state.get("error_message") or final_state.get("route") == "unknown":
            task.status = TaskStatus.FAILED
            task.output_text = final_state.get("error_message") or "Task could not be routed."
            log_level = LogLevel.ERROR
        else:
            task.status = TaskStatus.COMPLETED
            task.output_text = final_state.get("final_output")
            task.route_taken = final_state.get("route")
            log_level = LogLevel.INFO

        # Update the task in DB
        self.db.add(task)

        # 5. Write an Immutable Audit Log
        # This is critical for observability in agentic systems.
        log_entry = Log(
            task_id=task.id,
            message=f"Workflow completed with status: {task.status.value}",
            level=log_level,
            source="workflow_orchestrator",
            metadata_json={
                "route": final_state.get("route"),
                "error": final_state.get("error_message"),
                "agent": final_state.get("selected_agent")
            }
        )
        self.db.add(log_entry)

        await self.db.commit()
        await self.db.refresh(task)

        return task
