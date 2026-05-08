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
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.config.settings import get_settings
from app.models.gmail import OAuthToken
from app.core.exceptions import ValidationException

settings = get_settings()

# Scopes define EXACTLY what our app is allowed to do. We only need read/modify for Gmail.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",  # Read emails and mark as read/unread
]

class GoogleOAuthService:
    def __init__(self):
        # In a real enterprise system, credentials.json is securely injected via Secret Manager.
        # For this setup, we assume client_secret.json exists in the root or env vars.
        # Here we use a minimal placeholder or env-based config for the flow.
        self.client_config = {
            "web": {
                "client_id": settings.google_client_id if hasattr(settings, "google_client_id") else "PLACEHOLDER_ID",
                "client_secret": settings.google_client_secret if hasattr(settings, "google_client_secret") else "PLACEHOLDER_SECRET",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8000/api/v1/gmail/callback"]
            }
        }

    def get_authorization_url(self) -> str:
        """Generates the URL for the user to authorize our app."""
        flow = Flow.from_client_config(
            self.client_config, 
            scopes=GMAIL_SCOPES,
            redirect_uri="http://localhost:8000/api/v1/gmail/callback"
        )
        
        # access_type="offline" is CRITICAL to get a refresh_token
        # prompt="consent" forces Google to always return a refresh token
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true"
        )
        return auth_url

    async def exchange_code_for_token(self, db: AsyncSession, code: str, user_id: uuid.UUID) -> OAuthToken:
        """Exchanges the auth code for access/refresh tokens and saves to DB for the user."""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=GMAIL_SCOPES,
            redirect_uri="http://localhost:8000/api/v1/gmail/callback"
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

        from typing import cast
        token_record.access_token = cast(str, creds.token)
        if creds.refresh_token:
            token_record.refresh_token = cast(str, creds.refresh_token)
            
        token_record.scopes = cast(Optional[str], ",".join(creds.scopes) if creds.scopes else None)
        token_record.expires_at = cast(Optional[datetime], creds.expiry)

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
                from typing import cast
                token_record.access_token = cast(str, creds.token)
                token_record.expires_at = cast(Optional[datetime], creds.expiry)
                await db.commit()
            except Exception as e:
                raise ValidationException(f"Failed to refresh Google token: {str(e)}")

        if not creds.valid:
            raise ValidationException("Google credentials are invalid and could not be refreshed.")

        return creds
