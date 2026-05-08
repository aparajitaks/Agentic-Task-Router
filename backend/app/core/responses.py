"""
app/core/responses.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Clients should receive a consistent JSON envelope for EVERY response,
    whether success or failure.  Without this, each endpoint author invents
    their own shape.

WHAT IT DOES
    Provides:
      - success_response()  → wraps any data in {"success": true, "data": ...}
      - paginated_response() → adds pagination metadata
    Both return plain dicts that FastAPI serializes via its JSONResponse.

HOW IT CONNECTS
    app/routes/tasks.py  → imports and calls success_response() / paginated_response()
"""

from __future__ import annotations

from typing import Any, Optional


def success_response(
    data: Any,
    message: str = "Request completed successfully.",
    status_code: int = 200,
) -> dict:
    """
    Standard success envelope.

    Returns:
        {
          "success": true,
          "message": "...",
          "data": { ... }
        }
    """
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def paginated_response(
    data: Any,
    total: int,
    page: int,
    page_size: int,
    message: str = "Request completed successfully.",
) -> dict:
    """
    Paginated list envelope.

    Returns:
        {
          "success": true,
          "message": "...",
          "data": [...],
          "pagination": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5,
            "has_next": true,
            "has_prev": false
          }
        }
    """
    total_pages = max(1, -(-total // page_size))  # ceiling division
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
