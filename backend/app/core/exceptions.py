"""
app/core/exceptions.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    FastAPI's default error responses are framework-shaped and inconsistent.
    A production API must return a uniform JSON envelope for EVERY error so
    that clients (mobile apps, frontends, other services) never have to guess
    the shape of a failure response.

WHAT IT DOES
    1. Defines custom exception classes (AppException, NotFoundException, etc.)
    2. Provides exception handler functions that FastAPI registers at startup
    3. Wraps Pydantic's RequestValidationError into the same envelope
    4. Returns a consistent response shape:
       {
         "success": false,
         "error": {
           "code": "NOT_FOUND",
           "message": "Task with id 42 was not found",
           "details": null
         }
       }

HOW IT CONNECTS
    app/main.py  → calls register_exception_handlers(app) at startup
    app/services → raises AppException subclasses
    app/routes   → never catches exceptions — they bubble up to these handlers
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.core.exceptions")


# ─────────────────────────────────────────────────────────────────────────────
# Custom Exception Hierarchy
# ─────────────────────────────────────────────────────────────────────────────

class AppException(Exception):
    """
    Base class for all application-level exceptions.

    Subclass this for every domain error rather than raising plain Python
    exceptions or HTTPException directly inside service code.  This keeps
    business logic free of HTTP concepts.
    """

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist in the database."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictException(AppException):
    """Raised when creating a resource that already exists (duplicate)."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class ValidationException(AppException):
    """Raised for domain-level validation failures (beyond Pydantic schema)."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class UnauthorizedException(AppException):
    """Raised when authentication is required but not provided/valid."""

    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    """Raised when the authenticated user lacks permission for an action."""

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Response Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Build a uniform error JSON envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Exception Handlers
# ─────────────────────────────────────────────────────────────────────────────

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "AppException [%s]: %s | path=%s",
        exc.code,
        exc.message,
        request.url.path,
    )
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    logger.warning(
        "HTTPException [%s]: %s | path=%s",
        exc.status_code,
        exc.detail,
        request.url.path,
    )
    return _error_response(exc.status_code, "HTTP_ERROR", exc.detail)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic's validation errors into our standard envelope."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " → ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )
    logger.warning(
        "RequestValidationError | path=%s | errors=%s",
        request.url.path,
        errors,
    )
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="One or more request fields failed validation.",
        details=errors,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected server errors."""
    logger.exception(
        "Unhandled exception | path=%s | error=%s",
        request.url.path,
        str(exc),
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Registration Helper
# ─────────────────────────────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI application instance.

    Called once from app/main.py so that main.py stays clean.
    """
    app.add_exception_handler(AppException, app_exception_handler)          # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)       # type: ignore[arg-type]
