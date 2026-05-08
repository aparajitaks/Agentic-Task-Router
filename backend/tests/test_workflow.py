import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus

pytestmark = pytest.mark.asyncio

@patch("app.orchestrators.workflow_orchestrator.app_graph.ainvoke", new_callable=AsyncMock)
async def test_execute_workflow_success(
    mock_ainvoke,
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """
    Test executing an AI workflow through the API endpoint.
    Mocks the LangGraph execution to avoid hitting the OpenAI API during tests.
    """
    # Mock the returned state from LangGraph
    mock_ainvoke.return_value = {
        "route": "summarizer_agent",
        "selected_agent": "summarizer_agent",
        "final_output": "This is a mocked summary.",
        "error_message": None
    }

    payload = {
        "title": "Test AI Task",
        "input_text": "Please summarize this test data."
    }

    # Make the API call
    response = await async_client.post("/api/v1/tasks/execute", json=payload)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == payload["title"]
    assert data["input_text"] == payload["input_text"]
    assert data["output_text"] == "This is a mocked summary."
    assert data["route_taken"] == "summarizer_agent"
    assert data["status"] == "completed"

    task_id = data["id"]

    # Verify logs were generated
    logs_resp = await async_client.get(f"/api/v1/tasks/{task_id}/logs")
    assert logs_resp.status_code == 200
    logs_data = logs_resp.json()["data"]["logs"]
    assert len(logs_data) > 0
    assert logs_data[0]["level"] == "info"
    assert "Workflow completed" in logs_data[0]["message"]


@patch("app.orchestrators.workflow_orchestrator.app_graph.ainvoke", new_callable=AsyncMock)
async def test_execute_workflow_failure(
    mock_ainvoke,
    async_client: AsyncClient
):
    """
    Test handling an unknown route or execution failure.
    """
    mock_ainvoke.return_value = {
        "route": "unknown",
        "error_message": "Could not determine route."
    }

    payload = {
        "title": "Test AI Task Failure",
        "input_text": "Do something completely unrelated."
    }

    response = await async_client.post("/api/v1/tasks/execute", json=payload)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "failed"
    assert data["output_text"] == "Could not determine route."
