"""
app/core/auth.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Authentication is the first line of defense for a SaaS. This module
    manages user identity verification and provides the dependency used
    by routes to access the authenticated user.

WHAT IT DOES
    - Defines the `get_current_user` dependency.
    - Extracts identity from headers (mocking Clerk verification for now).
    - Ensures multi-tenant isolation by providing a verified User object.
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.config.settings import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

async def get_current_user(
    x_clerk_id: Optional[str] = Header(None, description="The Clerk ID of the authenticated user."),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the Clerk ID from the request headers
    and retrieves the corresponding User from the database.

    DEVELOPMENT BYPASS: If APP_ENV is 'development' and x_clerk_id is missing,
    we return a default 'demo_user_123' to unblock development/testing.
    """
    effective_clerk_id = x_clerk_id

    if not effective_clerk_id:
        if settings.app_env.lower() == "development":
            effective_clerk_id = "demo_user_123"
            logger.warning("No x-clerk-id header found. Bypassing auth in DEVELOPMENT mode with clerk_id: %s", effective_clerk_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: x-clerk-id header missing.",
            )

    stmt = select(User).where(User.clerk_id == effective_clerk_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Auto-create the user in development mode if missing
        if settings.app_env.lower() == "development" and effective_clerk_id == "demo_user_123":
            import uuid
            user = User(
                id=uuid.uuid4(),
                clerk_id=effective_clerk_id,
                email="demo@example.com",
                full_name="Demo Developer"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("Auto-created demo user for development mode.")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: User not found.",
            )

    return user
