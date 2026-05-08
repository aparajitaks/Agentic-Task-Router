"""
tests/test_tasks.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Every production API route needs tests.  These cover the happy paths and
    the most important error cases for the Task CRUD API.

    Tests act as executable documentation — they prove the API contract
    is being honoured.

WHAT IT TESTS
    - Create Task (201 response, correct fields)
    - List Tasks (paginated, correct shape)
    - Get Single Task (200 for existing, 404 for missing)
    - Update Task (title, status, invalid status transition)
    - Delete Task (soft-delete, verifying it disappears from list)
"""

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _create_task(client, title="Test Task", description="Test description") -> dict:
    """Helper to create a task and return the response data."""
    response = await client.post(
        "/api/v1/tasks/",
        json={"title": title, "description": description},
    )
    assert response.status_code == 201
    return response.json()["data"]


# ─────────────────────────────────────────────────────────────────────────────
# Create Task
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_success(async_client):
    """POST /api/v1/tasks/ should create a task and return 201."""
    response = await async_client.post(
        "/api/v1/tasks/",
        json={"title": "My First Task", "description": "Automate the boring stuff."},
    )
    assert response.status_code == 201
    body = response.json()

    assert body["success"] is True
    assert body["data"]["title"] == "My First Task"
    assert body["data"]["status"] == "pending"
    assert body["data"]["is_deleted"] is False
    assert "id" in body["data"]
    assert "created_at" in body["data"]


@pytest.mark.asyncio
async def test_create_task_missing_title(async_client):
    """POST /api/v1/tasks/ without a title should return 422."""
    response = await async_client.post(
        "/api/v1/tasks/",
        json={"description": "No title provided"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_task_blank_title(async_client):
    """POST /api/v1/tasks/ with blank title should return 422."""
    response = await async_client.post(
        "/api/v1/tasks/",
        json={"title": "   "},
    )
    assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# List Tasks
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tasks_empty(async_client):
    """GET /api/v1/tasks/ on empty DB should return empty list with pagination."""
    response = await async_client.get("/api/v1/tasks/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []
    assert body["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_list_tasks_returns_created_tasks(async_client):
    """After creating 3 tasks, list should return all 3."""
    for i in range(3):
        await _create_task(async_client, title=f"Task {i+1}")

    response = await async_client.get("/api/v1/tasks/")
    body = response.json()
    assert body["pagination"]["total"] == 3
    assert len(body["data"]) == 3


@pytest.mark.asyncio
async def test_list_tasks_pagination(async_client):
    """List tasks with page_size=2 should return only 2 items."""
    for i in range(5):
        await _create_task(async_client, title=f"Task {i+1}")

    response = await async_client.get("/api/v1/tasks/?page=1&page_size=2")
    body = response.json()
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["has_next"] is True
    assert body["pagination"]["has_prev"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Get Single Task
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_task_by_id_success(async_client):
    """GET /api/v1/tasks/{id} should return the task."""
    created = await _create_task(async_client, title="Find Me")
    task_id = created["id"]

    response = await async_client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["id"] == task_id
    assert body["data"]["title"] == "Find Me"


@pytest.mark.asyncio
async def test_get_task_not_found(async_client):
    """GET /api/v1/tasks/{id} for non-existent ID should return 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"/api/v1/tasks/{fake_id}")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"


# ─────────────────────────────────────────────────────────────────────────────
# Update Task
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_task_title(async_client):
    """PATCH /api/v1/tasks/{id} should update only the provided fields."""
    created = await _create_task(async_client)
    task_id = created["id"]

    response = await async_client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated Title"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_task_status_valid_transition(async_client):
    """PATCH status from pending → in_progress should succeed."""
    created = await _create_task(async_client)
    task_id = created["id"]

    response = await async_client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_task_invalid_status_transition(async_client):
    """PATCH status from pending → completed (invalid) should return 422."""
    created = await _create_task(async_client)
    task_id = created["id"]

    response = await async_client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "completed"},   # Must go pending → in_progress → completed
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ─────────────────────────────────────────────────────────────────────────────
# Delete Task
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_task_success(async_client):
    """DELETE /api/v1/tasks/{id} should soft-delete (not hard-delete)."""
    created = await _create_task(async_client)
    task_id = created["id"]

    # Delete
    response = await async_client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200

    # Verify it no longer appears in list
    list_response = await async_client.get("/api/v1/tasks/")
    assert list_response.json()["pagination"]["total"] == 0

    # Verify direct GET also returns 404
    get_response = await async_client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 404
