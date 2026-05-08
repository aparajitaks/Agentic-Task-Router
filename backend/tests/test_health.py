"""
tests/test_health.py
─────────────────────────────────────────────────────────────────────────────
Tests for the health check endpoints.
These are the most basic tests — if these fail, something is fundamentally wrong.
"""

import pytest


@pytest.mark.asyncio
async def test_liveness_check(async_client):
    """GET /health should return 200 with the service metadata."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert "version" in body["data"]
    assert "environment" in body["data"]
