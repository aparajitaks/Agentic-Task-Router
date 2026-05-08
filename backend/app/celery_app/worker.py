"""
app/celery_app/worker.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This is the entrypoint for Celery. It initializes the Celery application
    using the configuration provided by our Pydantic settings.

WHAT IT DOES
    - Connects to the Redis broker (where tasks are queued).
    - Connects to the Redis result backend (where task outcomes are stored).
    - Autodiscovers tasks registered in `app.workers.tasks`.

HOW IT CONNECTS
    The docker-compose `worker` service runs:
    `celery -A app.celery_app.worker.celery_app worker`
"""

from celery import Celery
from app.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "agentic_router_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Production best practices
    worker_prefetch_multiplier=1,  # Good for long-running AI tasks
    task_acks_late=True,           # Don't acknowledge task until finished
)
