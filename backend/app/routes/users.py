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
"""

import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.core.responses import success_response

router = APIRouter(prefix="/users", tags=["Users & SaaS Management"])

# ── Schemas ─────────────────────────────────────────────────────────────────

class UserSyncRequest(BaseModel):
    clerk_id: str
    email: str
    full_name: Optional[str] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    has_completed_onboarding: Optional[bool] = None
    preferences: Optional[dict] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    clerk_id: str
    email: str
    full_name: Optional[str] = None
    has_completed_onboarding: bool
    preferences: Optional[dict] = None
    
    model_config = {"from_attributes": True}

# ── Routes ──────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns the profile of the currently authenticated user."""
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(mode="json"), 
        message="Profile retrieved"
    )

@router.post("/sync-user")
async def sync_clerk_user(
    body: UserSyncRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
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
    
    return success_response(
        data=UserResponse.model_validate(user).model_dump(mode="json"), 
        message="User synchronized"
    )

@router.patch("/me")
async def update_user_profile(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates the user's profile metadata or onboarding state."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.has_completed_onboarding is not None:
        current_user.has_completed_onboarding = body.has_completed_onboarding
    if body.preferences is not None:
        current_prefs = current_user.preferences if isinstance(current_user.preferences, dict) else {}
        current_user.preferences = {**current_prefs, **body.preferences}
        
    await db.commit()
    await db.refresh(current_user)
    
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(mode="json"), 
        message="Profile updated"
    )
