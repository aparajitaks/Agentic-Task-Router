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

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import sqlalchemy as sa
from typing import cast
import uuid

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.oauth.google import GoogleOAuthService
from app.ingestion.email_ingester import EmailIngester
from app.models.gmail import OAuthToken, EmailMessage
from app.core.responses import success_response, paginated_response

router = APIRouter(prefix="/gmail", tags=["Gmail Integration"])


@router.get("/connect", summary="Get Google Auth URL")
async def connect_gmail() -> dict:
    """Returns the OAuth2 URL that the user must visit to grant Gmail access."""
    oauth_service = GoogleOAuthService()
    url = oauth_service.get_authorization_url()
    return success_response(data={"auth_url": url}, message="Please visit the URL to authenticate.")


@router.get("/callback", summary="OAuth Callback")
async def gmail_callback(
    code: str = Query(..., description="The authorization code from Google"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Handles the redirect from Google and stores the OAuth tokens."""
    oauth_service = GoogleOAuthService()
    await oauth_service.exchange_code_for_token(db, code, current_user.id)
    return success_response(data={}, message="Gmail connected successfully! You can close this window.")


@router.get("/status", summary="Check Integration Status")
async def gmail_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
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
) -> dict:
    """Revokes Gmail OAuth tokens and disconnects the integration."""
    stmt = select(OAuthToken).where(
        OAuthToken.provider == "google",
        OAuthToken.user_id == current_user.id
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    
    if token:
        # REAL DISCONNECT: Revoke the token from Google's servers
        import httpx
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
                    logger.warning(f"Google token revocation returned status {revoke_res.status_code}: {revoke_res.text}")
        except Exception as e:
            # We don't block DB deletion if Google revocation fails (e.g. token already expired)
            logger.error(f"Error during Google token revocation: {str(e)}")

        await db.delete(token)
        await db.commit()
        return success_response(data={"connected": False}, message="Gmail disconnected and tokens revoked.")
    
    return success_response(data={"connected": False}, message="Not connected to Gmail.")


@router.post("/sync", summary="Trigger Email Ingestion")
async def sync_emails(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
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
) -> dict:
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
