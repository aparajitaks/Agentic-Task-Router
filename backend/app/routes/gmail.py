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

HOW IT CONNECTS
    Included in `app.main` as `/api/v1/gmail`. Calls `GoogleOAuthService` and
    `EmailIngester`.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.core.responses import success_response
from app.oauth.google import GoogleOAuthService
from app.ingestion.email_ingester import EmailIngester
from app.models.gmail import OAuthToken

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
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Handles the redirect from Google and stores the OAuth tokens."""
    oauth_service = GoogleOAuthService()
    await oauth_service.exchange_code_for_token(db, code)
    return success_response(data={}, message="Gmail connected successfully! You can close this window.")


@router.get("/status", summary="Check Integration Status")
async def gmail_status(db: AsyncSession = Depends(get_db)) -> dict:
    """Checks if the system has valid Gmail OAuth tokens."""
    stmt = select(OAuthToken).where(OAuthToken.provider == "google")
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


@router.post("/sync", summary="Trigger Email Ingestion")
async def sync_emails(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Manually triggers the pipeline to fetch unread emails, parse them,
    and queue them for AI processing.
    """
    ingester = EmailIngester(db)
    count = await ingester.sync_unread_emails()
    
    return success_response(
        data={"emails_processed": count},
        message=f"Successfully ingested {count} unread emails."
    )
