"""
app/utils/middleware.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Middleware runs on EVERY request/response cycle — perfect for cross-cutting
    concerns that shouldn't pollute individual route handlers:
      - Request ID generation (for distributed tracing)
      - Request/response logging with timing
      - Future: rate limiting, authentication token introspection

WHAT IT DOES
    RequestLoggingMiddleware:
      - Generates a unique X-Request-ID for every request
      - Logs incoming requests with method, path, and client IP
      - Logs outgoing responses with status code and processing time (ms)
      - Attaches X-Request-ID and X-Process-Time to response headers

HOW IT CONNECTS
    app/main.py  → app.add_middleware(RequestLoggingMiddleware)
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request and response with timing and a unique request ID.

    The X-Request-ID header is useful for correlating logs across microservices
    and for debugging production issues reported by users.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate or propagate a request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        # Log the incoming request
        logger.info(
            "→ %s %s | client=%s | request_id=%s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
            request_id,
        )

        # Process the request
        response: Response = await call_next(request)

        # Calculate processing time
        process_time_ms = (time.perf_counter() - start_time) * 1000

        # Log the outgoing response
        logger.info(
            "← %s %s | status=%d | took=%.2fms | request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            process_time_ms,
            request_id,
        )

        # Attach metadata to response headers for clients/proxies
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"

        return response
