"""
app/gmail/client.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The raw Google API python client is powerful but incredibly verbose and 
    complex. This file acts as a Facade. It wraps the raw Google API calls into
    clean, domain-specific Python methods.

WHAT IT DOES
    - `build_service()`: Creates the `googleapiclient` Resource.
    - `fetch_unread_emails()`: Retrieves the IDs of unread emails.
    - `get_email_details()`: Downloads the full payload of a specific email.
    - `mark_as_read()`: Removes the "UNREAD" label so we don't process it twice.

HOW IT CONNECTS
    The `EmailIngester` service uses this client to interact with Gmail, completely
    ignorant of the underlying `googleapiclient` HTTP details.
"""

from typing import List, Dict, Any
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GmailClient:
    def __init__(self, credentials: Credentials):
        """Initializes the Gmail API service using valid OAuth2 credentials."""
        self.service = build('gmail', 'v1', credentials=credentials)

    def fetch_unread_emails(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Fetches a list of unread email IDs and Thread IDs.
        
        Returns:
            List of dicts: [{'id': 'message_id', 'threadId': 'thread_id'}, ...]
        """
        # Query Gmail for messages with the UNREAD label in the inbox.
        results = self.service.users().messages().list(
            userId='me', 
            labelIds=['INBOX', 'UNREAD'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        return messages

    def get_email_details(self, message_id: str) -> Dict[str, Any]:
        """
        Fetches the complete payload of a specific email by its ID.
        Uses format='full' to retrieve headers, body, and MIME parts.
        """
        return self.service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()

    def mark_as_read(self, message_id: str) -> None:
        """
        Removes the 'UNREAD' label from an email to prevent duplicate ingestion.
        """
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
