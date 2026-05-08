"""
app/routes/users.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The central API for managing User profiles and SaaS-specific metadata.
    This is where the frontend syncs Clerk identity and manages Gmail tokens.

WHAT IT DOES
    - GET  /me          → Returns the current user's profile and settings.
    - PATCH /me         → Updates user preferences and onboarding state.
    - POST /sync-user   → Synchronizes the Clerk user with our database.
    - POST /connect-gmail → Stores and validates Gmail OAuth tokens.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.core.responses import success_response
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users & SaaS Management"])

class UserSyncRequest(BaseModel):
    clerk_id: str
    email: str
    full_name: Optional[str] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    has_completed_onboarding: Optional[bool] = None
    preferences: Optional[dict] = None

@router.get("/me")
async def get_current_user_profile(
    user: User = Depends(get_current_user)
):
    return success_response(data=user, message="Profile retrieved")

@router.post("/sync-user")
async def sync_clerk_user(
    body: UserSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Called by the frontend after a successful Clerk signup/login to ensure
    the user exists in our local database.
    """
    stmt = select(User).where(User.clerk_id == body.clerk_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            id=uuid.uuid4(),
            clerk_id=body.clerk_id,
            email=body.email,
            full_name=body.full_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return success_response(data=user, message="User synchronized")

@router.patch("/me")
async def update_user_profile(
    body: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.has_completed_onboarding is not None:
        user.has_completed_onboarding = body.has_completed_onboarding
    if body.preferences is not None:
        current_prefs = user.preferences if isinstance(user.preferences, dict) else {}
        user.preferences = {**current_prefs, **body.preferences}
        
    await db.commit()
    await db.refresh(user)
    
    return success_response(data=user, message="Profile updated")
