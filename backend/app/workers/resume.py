"""
app/workers/resume.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    When a human approves/edits a workflow, the LangGraph execution must RESUME
    from the exact checkpoint where it was paused. This cannot happen in the
    HTTP request-response cycle (too slow, blocking), so it must be dispatched
    as a new Celery background task.

    This is the architectural keystone of HITL: the approval API triggers this
    worker, which rebuilds the graph state from the persisted checkpoint and
    continues execution from the `human_review_node` forward.

WHAT IT DOES
    - `resume_workflow_task`: The Celery task that receives a checkpoint dict
      and the approved/edited final content, then re-runs the graph from that
      state forward.
    - `ResumeWorkflowEngine`: A specialized engine variant that injects the
      human decision into the WorkflowState and calls `astream` from the
      correct graph node.

HOW IT CONNECTS
    - app/services/approval.py  → Calls `.delay()` on `resume_workflow_task`
    - app/graphs/main_graph.py  → Imports the graph for resumed execution
    - app/models/approval.py    → Updates `resumed_at` after successful resumption
    - app/models/task.py        → Final task status set to COMPLETED or FAILED
"""

import asyncio
from celery import Task as CeleryTask

from app.celery_app.worker import celery_app
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


class ResumeWorkflowTask(CeleryTask):
    """Base class for the resume task to handle persistent failures."""
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "Resume task %s FAILED permanently: %s",
            task_id, exc,
            exc_info=True,
        )


async def _async_resume_workflow(
    task_id_str: str,
    approval_id_str: str,
    checkpoint_state: dict,
) -> None:
    """
    Async inner function that performs the actual graph resumption.

    Strategy:
    1. Load the checkpoint state (which already has `final_output` injected
       by the approval service with the human's approved/edited content).
    2. Re-run the graph from the `send_email_node` forward (or END, if the
       workflow was configured to finish after human review).
    3. Update the Task's final status in the database.
    """
    import uuid
    from langchain_core.messages import messages_from_dict
    from app.graphs.hitl_graph import hitl_graph
    from app.models.task import Task, TaskStatus
    from app.models.approval import Approval
    from app.models.log import Log, LogLevel

    task_id = uuid.UUID(task_id_str)
    approval_id = uuid.UUID(approval_id_str)

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        try:
            logger.info(
                "Resuming workflow | task_id=%s approval_id=%s",
                task_id_str, approval_id_str,
            )

            # ── Reconstruct the WorkflowState from the checkpoint ─────────────
            workflow_state = checkpoint_state
            
            # Restore LangChain message objects
            if "messages" in workflow_state and workflow_state["messages"]:
                workflow_state["messages"] = messages_from_dict(workflow_state["messages"])

            logger.info(
                "Resuming LangGraph execution | task_id=%s final_output_length=%d",
                task_id_str,
                len(workflow_state.get("final_output", "") or ""),
            )

            # ── Forge Graph State & Resume Execution ──────────────────────────
            config = {"configurable": {"thread_id": task_id_str}}
            
            # Inject the restored state (with human edits) into the checkpointer 
            # as if it just came out of the human_review_node
            hitl_graph.update_state(config, workflow_state, as_node="human_review_node")
            
            # Invoke the graph. Since the state is paused at human_review_node,
            # it will automatically traverse the edge to send_email_node and then END.
            final_state = await hitl_graph.ainvoke(None, config)

            # ── Update Task to COMPLETED ──────────────────────────────────────
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if task:
                from datetime import datetime, timezone
                if final_state.get("error_message"):
                    task.status = TaskStatus.FAILED
                    task.failure_reason = final_state.get("error_message")
                else:
                    task.status = TaskStatus.COMPLETED
                    task.output_text = final_state.get("final_output")
                
                task.execution_completed_at = datetime.now(timezone.utc)
                
                db.add(Log(
                    task_id=task.id,
                    message=f"Resumed workflow finished: {task.status.value}",
                    level=LogLevel.INFO if task.status == TaskStatus.COMPLETED else LogLevel.ERROR,
                    source="celery_worker"
                ))

            # ── Mark Approval as resumed ──────────────────────────────────────
            approval_stmt = select(Approval).where(Approval.id == approval_id)
            approval_result = await db.execute(approval_stmt)
            approval = approval_result.scalar_one_or_none()
            if approval and not approval.resumed_at:
                from datetime import datetime, timezone
                approval.resumed_at = datetime.now(timezone.utc)

            await db.commit()
            logger.info(
                "Workflow resumed and completed | task_id=%s", task_id_str
            )

        except Exception as exc:
            logger.error(
                "Resume workflow failed | task_id=%s error=%s",
                task_id_str, str(exc),
                exc_info=True,
            )
            # Mark task as failed on resume error
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()
            if task:
                task.status = TaskStatus.FAILED
                task.failure_reason = f"Resume execution error: {str(exc)}"
            await db.commit()
            raise


@celery_app.task(
    bind=True,
    base=ResumeWorkflowTask,
    name="app.workers.resume.resume_workflow_task",
    max_retries=2,
    default_retry_delay=10,
)
def resume_workflow_task(
    self,
    task_id_str: str,
    approval_id_str: str,
    checkpoint_state: dict,
):
    """
    Celery task that resumes a LangGraph workflow after human approval.

    Args:
        task_id_str:      The UUID string of the Task to resume.
        approval_id_str:  The UUID string of the Approval record.
        checkpoint_state: The serialized WorkflowState dict with human
                          decision injected at `final_output`.
    """
    logger.info(
        "Resume worker picked up | task_id=%s approval_id=%s",
        task_id_str, approval_id_str,
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _async_resume_workflow(task_id_str, approval_id_str, checkpoint_state)
        )
    except Exception as exc:
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)
        logger.warning(
            "Resume task failed, scheduling retry | countdown=%ds error=%s",
            retry_delay, str(exc),
        )
        raise self.retry(exc=exc, countdown=retry_delay)
    finally:
        loop.close()
