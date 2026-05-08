import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.execution_engine.engine import SyncWorkflowEngine

pytestmark = pytest.mark.asyncio

@patch("app.routes.tasks.execute_agentic_workflow_task.delay")
async def test_execute_workflow_api_queues_task(
    mock_delay,
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """
    Test that the POST /execute endpoint successfully creates a Task in the DB
    with status QUEUED and calls the Celery task delay method.
    """
    payload = {
        "title": "Test AI Task Queue",
        "input_text": "Please summarize this test data."
    }

    # Make the API call
    response = await async_client.post("/api/v1/tasks/execute", json=payload)
    
    assert response.status_code == 202
    data = response.json()["data"]
    assert data["title"] == payload["title"]
    assert data["input_text"] == payload["input_text"]
    assert data["status"] == "queued"

    # Verify celery task was triggered
    task_id = data["id"]
    mock_delay.assert_called_once_with(task_id)


@patch("app.execution_engine.engine.app_graph.ainvoke", new_callable=AsyncMock)
@patch("app.execution_engine.engine.AsyncSessionLocal")
async def test_sync_workflow_engine_success(
    mock_session_local,
    mock_ainvoke,
    db_session: AsyncSession
):
    """
    Test the SyncWorkflowEngine (used by Celery) handles a successful graph execution.
    """
    # Configure the mock to return our pytest db_session
    mock_session_local.return_value.__aenter__.return_value = db_session
    # 1. Create a raw queued task
    task = Task(
        title="Engine Test",
        input_text="Do work",
        status=TaskStatus.QUEUED
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 2. Mock graph
    mock_ainvoke.return_value = {
        "route": "summarizer_agent",
        "selected_agent": "summarizer_agent",
        "final_output": "Mocked sync engine output.",
        "error_message": None
    }

    # 3. Run engine's async method directly since pytest-asyncio already has a loop
    engine = SyncWorkflowEngine()
    await engine._async_run_workflow(str(task.id), "worker-test-1")

    # 4. Verify DB updates
    await db_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert task.output_text == "Mocked sync engine output."
    assert task.route_taken == "summarizer_agent"
    assert task.worker_id == "worker-test-1"
    assert task.execution_completed_at is not None
