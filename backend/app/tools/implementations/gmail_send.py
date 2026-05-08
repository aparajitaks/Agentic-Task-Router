"""
app/tools/implementations/gmail_send.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    For a fully autonomous system, agents must be able to take external actions.
    This tool allows an agent to draft and send emails directly through the user's
    connected Gmail account.

WHAT IT DOES
    - Takes a recipient email, subject, and body.
    - Uses the existing `GoogleOAuthService` to get a valid token.
    - Uses the `gmail` API client to dispatch the email.
"""

import base64
from email.message import EmailMessage
from langchain_core.tools import tool
from googleapiclient.discovery import build
import asyncio

from app.oauth.google import GoogleOAuthService
from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

async def _send_email_async(to: str, subject: str, body: str) -> str:
    """Async helper to connect to DB and send email."""
    try:
        oauth_service = GoogleOAuthService()
        async with AsyncSessionLocal() as db:
            creds = await oauth_service.get_valid_credentials(db)
        
        service = build('gmail', 'v1', credentials=creds)
        
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        # Execute the send
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return f"Email sent successfully. Message Id: {send_message['id']}"
        
    except Exception as e:
        logger.error(f"Gmail Send Tool Error: {e}")
        return f"Failed to send email: {str(e)}"

@tool
def gmail_send_tool(recipient: str, subject: str, body: str) -> str:
    """
    Sends an email using the connected Gmail account.
    Use this to reply to users or send notifications.
    Inputs required:
    - recipient: The email address to send to.
    - subject: The subject line of the email.
    - body: The full text body of the email.
    """
    logger.info(f"Agent attempting to send email to {recipient}")
    
    # Run the async helper synchronously inside the worker thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_send_email_async(recipient, subject, body))
        return result
    finally:
        loop.close()
