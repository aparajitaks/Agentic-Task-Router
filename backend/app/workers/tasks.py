"""
app/workers/tasks.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Defines the background tasks that Celery workers will execute. This moves
    the slow, blocking LLM work out of the FastAPI request-response cycle.

WHAT IT DOES
    - Defines `execute_agentic_workflow_task` which takes a `task_id`.
    - Handles retries (e.g., if OpenAI API rate limits us).
    - Calls the synchronous execution engine wrapper.

HOW IT CONNECTS
    Called by FastAPI `app/routes/tasks.py` via `.delay(task_id)` to enqueue.
"""

import asyncio
from celery import Task
from app.celery_app.worker import celery_app
from app.execution_engine.engine import SyncWorkflowEngine
from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

async def _async_poll_gmail():
    from app.ingestion.email_ingester import EmailIngester
    from app.models.user import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        # Fetch all users to poll their respective Gmail accounts
        stmt = select(User)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        total_processed = 0
        for user in users:
            try:
                # Ingester is now scoped to a specific user
                ingester = EmailIngester(db, user.id)
                count = await ingester.sync_unread_emails()
                total_processed += count
            except Exception as e:
                logger.error(f"Error polling Gmail for user {user.id}: {str(e)}")
                
        return total_processed

class AgenticWorkflowTask(Task):
    """Base class for our tasks to handle common logic like retries."""
    abstract = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed permanently: {exc}")

@celery_app.task(
    bind=True,
    base=AgenticWorkflowTask,
    max_retries=3,
    default_retry_delay=5,  # 5 seconds initial delay, can use exponential backoff
)
def execute_agentic_workflow_task(self, task_id_str: str):
    """
    Executes the LangGraph workflow for a given database Task ID.
    """
    logger.info(f"Worker picked up task: {task_id_str}")
    
    engine = SyncWorkflowEngine()
    
    try:
        # Run the workflow synchronously since Celery is sync
        engine.run_workflow(task_id_str, worker_id=self.request.hostname)
    except Exception as exc:
        logger.warning(f"Error executing task {task_id_str}. Retrying...")
        # Update retry count in DB if needed (handled in engine or here)
        # Exponential backoff: 5s, 10s, 20s
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=retry_delay)


@celery_app.task(bind=True, max_retries=3)
def poll_gmail_inbox(self):
    """
    Background polling task that checks Gmail for new unread emails
    and queues them into the LangGraph system.
    """
    logger.info("Polling Gmail for unread emails...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        count = loop.run_until_complete(_async_poll_gmail())
        logger.info(f"Successfully processed {count} new emails.")
    except Exception as exc:
        logger.error(f"Failed to poll Gmail: {str(exc)}")
        raise self.retry(exc=exc, countdown=10)
    finally:
        loop.close()
