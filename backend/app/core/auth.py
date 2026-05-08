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

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User

async def get_current_user(
    x_clerk_id: str = Header(..., description="The Clerk ID of the authenticated user."),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the Clerk ID from the request headers
    and retrieves the corresponding User from the database.

    In a production Clerk integration, this would involve verifying a
    JWT token (Bearer token) using Clerk's public keys.
    """
    stmt = select(User).where(User.clerk_id == x_clerk_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: User not found in local database. Please sync your account.",
            headers={"WWW-Authenticate": "Header"},
        )

    return user
