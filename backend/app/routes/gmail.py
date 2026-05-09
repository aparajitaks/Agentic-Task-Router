"""
app/routes/gmail.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Exposes the Gmail integration via REST API endpoints. This allows administrators
    or frontend clients to connect a Google account, check integration status,
    and manually trigger email ingestion.

WHAT IT DOES
    - `GET /connect`: Returns the Google OAuth2 authorization URL.
    - `GET /callback`: Handles the redirect from Google, saving tokens.
    - `POST /sync`: Manually triggers the EmailIngester pipeline.
    - `GET /status`: Checks if the system is currently authenticated with Gmail.
    - `GET /emails`: Lists ingested email messages for the current user.

HOW IT CONNECTS
    Included in `app.main` as `/api/v1/gmail`. Calls `GoogleOAuthService` and
    `EmailIngester`.
"""

import uuid
import httpx
import sqlalchemy as sa
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import get_settings
from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.oauth.google import GoogleOAuthService
from app.ingestion.email_ingester import EmailIngester
from app.models.gmail import OAuthToken, EmailMessage
from app.core.responses import success_response, paginated_response
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(prefix="/gmail", tags=["Gmail Integration"])


import json
import base64

@router.get("/connect", summary="Get Google Auth URL")
async def connect_gmail(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Returns the OAuth2 URL that the user must visit to grant Gmail access.
    
    We encode the current user's clerk_id into the 'state' parameter.
    Google will pass this state back to our /callback endpoint.
    This allows us to identify the user even though the callback
    request won't have authentication headers (x-clerk-id).
    """
    oauth_service = GoogleOAuthService()
    
    # Create a state object containing the user's clerk_id
    state_data = {"clerk_id": current_user.clerk_id}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    
    url = oauth_service.get_authorization_url(state=state)
    return success_response(data={"auth_url": url}, message="Please visit the URL to authenticate.")


@router.get("/callback", summary="OAuth Callback")
async def gmail_callback(
    code: str = Query(..., description="The authorization code from Google"),
    state: str = Query(..., description="The state parameter containing user info"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Handles the redirect from Google and stores the OAuth tokens.
    
    CRITICAL: This endpoint is called directly by Google's servers/redirects.
    It DOES NOT receive the x-clerk-id header. We must resolve the user
    via the 'state' parameter.
    """
    logger.info("Received Google OAuth callback. State: %s", state)
    
    try:
        # Decode the state to get the user's clerk_id
        state_json = base64.urlsafe_b64decode(state.encode()).decode()
        state_data = json.loads(state_json)
        clerk_id = state_data.get("clerk_id")
        
        if not clerk_id:
            logger.error("OAuth callback failed: clerk_id missing from state.")
            return RedirectResponse(url=f"{settings.frontend_url}/dashboard?auth_error=state_missing")

        # Resolve the user from the database
        stmt = select(User).where(User.clerk_id == clerk_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("OAuth callback failed: No user found for clerk_id %s", clerk_id)
            return RedirectResponse(url=f"{settings.frontend_url}/dashboard?auth_error=user_not_found")

        logger.info("Resolved user %s from OAuth state. Exchanging code...", user.id)

        # Exchange code for tokens and save
        oauth_service = GoogleOAuthService()
        await oauth_service.exchange_code_for_token(db, code, user.id)
        
        logger.info("Successfully linked Google OAuth token for user %s", user.id)
        
        # Redirect back to the frontend dashboard with success flag
        return RedirectResponse(url=f"{settings.frontend_url}/dashboard?auth_success=true")

    except Exception as e:
        logger.error("Google OAuth callback failed: %s", str(e))
        return RedirectResponse(url=f"{settings.frontend_url}/dashboard?auth_error=exception")


@router.get("/status", summary="Check Integration Status")
async def gmail_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Checks if the system has valid Gmail OAuth tokens."""
    stmt = select(OAuthToken).where(
        OAuthToken.user_id == current_user.id
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if not token:
        return success_response(data={"connected": False}, message="Not connected to Gmail.")
    
    return success_response(
        data={
            "connected": True,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scopes": token.scopes.split(",") if token.scopes else []
        },
        message="Gmail integration is active."
    )


@router.post("/disconnect", summary="Disconnect Gmail")
async def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Revokes Gmail OAuth tokens and disconnects the integration."""
    stmt = select(OAuthToken).where(
        OAuthToken.provider == "google",
        OAuthToken.user_id == current_user.id
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    
    if token:
        # REAL DISCONNECT: Revoke the token from Google's servers
        try:
            async with httpx.AsyncClient() as client:
                # We prioritize revoking the refresh_token as it's more durable, 
                # but access_token works too if refresh is missing.
                revoke_target = token.refresh_token or token.access_token
                revoke_res = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": revoke_target},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if revoke_res.status_code == 200:
                    logger.info(f"Google OAuth token revoked for user: {current_user.id}")
                else:
                    logger.warning(
                        "Google token revocation returned status %d: %s",
                        revoke_res.status_code,
                        revoke_res.text
                    )
        except Exception as e:
            # We don't block DB deletion if Google revocation fails (e.g. token already expired)
            logger.error(f"Error during Google token revocation for user {current_user.id}: {str(e)}")

        await db.delete(token)
        await db.commit()
        return success_response(data={"connected": False}, message="Gmail disconnected and tokens revoked.")
    
    return success_response(data={"connected": False}, message="Not connected to Gmail.")


@router.post("/sync", summary="Trigger Email Ingestion")
async def sync_emails(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Manually triggers the pipeline to fetch unread emails for the current user.
    """
    ingester = EmailIngester(db, user_id=current_user.id)
    count = await ingester.sync_unread_emails()
    
    return success_response(
        data={"emails_processed": count},
        message=f"Successfully ingested {count} unread emails."
    )


@router.get("/emails", summary="List Ingested Emails")
async def list_ingested_emails(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Returns a list of emails that have been ingested for the current user."""
    offset = (page - 1) * page_size
    
    # Count total
    count_stmt = select(sa.func.count()).select_from(EmailMessage).where(EmailMessage.user_id == current_user.id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Fetch messages
    stmt = select(EmailMessage).where(EmailMessage.user_id == current_user.id).order_by(EmailMessage.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return paginated_response(
        data=[{
            "id": str(m.id),
            "gmail_message_id": m.gmail_message_id,
            "sender": m.sender_email,
            "subject": m.subject,
            "status": m.status,
            "task_id": str(m.task_id) if m.task_id else None,
            "received_at": m.received_at.isoformat(),
        } for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        message="Ingested emails retrieved."
    )
