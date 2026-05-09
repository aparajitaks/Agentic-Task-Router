"""
app/oauth/google.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    To connect to Gmail, we must act on behalf of a user. Google requires OAuth2.
    This module centralizes the OAuth2 dance: generating authorization URLs,
    exchanging codes for tokens, and refreshing expired tokens automatically.

WHAT IT DOES
    - `get_authorization_url()`: Creates the URL the user must visit to grant access.
    - `exchange_code_for_token()`: Takes the callback code and gets access/refresh tokens.
    - `get_valid_credentials()`: Retrieves credentials from the DB, auto-refreshing if expired.

HOW IT CONNECTS
    The `app.routes.gmail` endpoints will use this to implement the `/connect` and
    `/callback` endpoints. The `app.gmail.client` will use `get_valid_credentials()`
    to authenticate its API requests.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.config.settings import get_settings
from app.models.gmail import OAuthToken
from app.core.exceptions import ValidationException

from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Scopes define EXACTLY what our app is allowed to do. We only need read/modify for Gmail.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",  # Read emails and mark as read/unread
]

class GoogleOAuthService:
    def __init__(self):
        """
        Initializes the Google OAuth Flow configuration.
        
        CRITICAL: We MUST ensure client_id and client_secret are loaded from env.
        If they are missing or still 'PLACEHOLDER', the OAuth flow will fail.
        """
        # Validate settings on init
        client_id = settings.google_client_id
        client_secret = settings.google_client_secret
        
        if not client_id or "PLACEHOLDER" in client_id:
            logger.error("CRITICAL: GOOGLE_CLIENT_ID is missing or invalid!")
        else:
            logger.info("Google OAuth Client ID loaded: %s...", client_id[:15])

        if not client_secret or "PLACEHOLDER" in client_secret:
            logger.error("CRITICAL: GOOGLE_CLIENT_SECRET is missing or invalid!")
        
        self.client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri]
            }
        }

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generates the URL for the user to authorize our app.
        
        The 'state' parameter is used to maintain state between the request and the callback,
        acting as a CSRF protection and a way to pass user identifiers (like clerk_id)
        back to the callback route which won't have authentication headers.
        """
        if not self.client_config["web"]["client_id"]:
            raise ValidationException("Google Client ID is not configured. Please check environment variables.")

        flow = Flow.from_client_config(
            self.client_config, 
            scopes=GMAIL_SCOPES,
            redirect_uri=settings.google_redirect_uri
        )
        
        # access_type="offline" is CRITICAL to get a refresh_token
        # prompt="consent" forces Google to always return a refresh token
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state
        )
        return auth_url

    async def exchange_code_for_token(self, db: AsyncSession, code: str, user_id: uuid.UUID) -> OAuthToken:
        """Exchanges the auth code for access/refresh tokens and saves to DB for the user."""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=GMAIL_SCOPES,
            redirect_uri=settings.google_redirect_uri
        )
        
        try:
            flow.fetch_token(code=code)
        except Exception as e:
            raise ValidationException(f"Failed to exchange auth code: {str(e)}")

        creds = flow.credentials

        # Upsert the token into the database for this specific user
        stmt = select(OAuthToken).where(
            OAuthToken.provider == "google",
            OAuthToken.user_id == user_id
        )
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            token_record = OAuthToken(provider="google", user_id=user_id)
            db.add(token_record)
        token_record.access_token = cast(str, creds.token)
        if creds.refresh_token:
            token_record.refresh_token = cast(str, creds.refresh_token)
            
        token_record.scopes = ",".join(creds.scopes) if creds.scopes else None  # type: ignore[assignment]
        token_record.expires_at = creds.expiry  # type: ignore[assignment]

        await db.commit()
        await db.refresh(token_record)
        return token_record

    async def get_valid_credentials(self, db: AsyncSession, user_id: uuid.UUID) -> Credentials:
        """
        Retrieves credentials from the DB for a specific user. Automatically refreshes them if expired.
        Raises ValidationException if no tokens exist or refresh fails.
        """
        stmt = select(OAuthToken).where(
            OAuthToken.provider == "google",
            OAuthToken.user_id == user_id
        )
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise ValidationException("Google OAuth is not connected. Please authenticate first.")

        creds = Credentials(
            token=token_record.access_token,
            refresh_token=token_record.refresh_token,
            token_uri=self.client_config["web"]["token_uri"],
            client_id=self.client_config["web"]["client_id"],
            client_secret=self.client_config["web"]["client_secret"],
            scopes=token_record.scopes.split(",") if token_record.scopes else GMAIL_SCOPES
        )

        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update the DB with the new access token
                token_record.access_token = cast(str, creds.token)
                token_record.expires_at = creds.expiry  # type: ignore[assignment]
                await db.commit()
            except Exception as e:
                raise ValidationException(f"Failed to refresh Google token: {str(e)}")

        if not creds.valid:
            raise ValidationException("Google credentials are invalid and could not be refreshed.")

        return creds
