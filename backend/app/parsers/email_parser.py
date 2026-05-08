"""
app/parsers/email_parser.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Gmail API returns emails in a complex, nested MIME structure encoded in Base64.
    This file abstracts the messiness of parsing multipart MIME bodies and extracting
    clean text for our AI agents to read.

WHAT IT DOES
    - Base64 decodes email parts.
    - Traverses nested payloads to find the 'text/plain' or 'text/html' body.
    - Extracts critical headers (From, Subject, Date).

HOW IT CONNECTS
    Called by the EmailIngester after fetching a raw email from GmailClient.
"""

import base64
from typing import Dict, Any, Optional

class EmailParser:
    @staticmethod
    def _decode_base64(data: str) -> str:
        """Helper to decode base64url encoded strings from Gmail API."""
        if not data:
            return ""
        # Gmail API uses urlsafe base64 encoding
        padded_data = data + '=' * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(padded_data).decode('utf-8', errors='ignore')

    @classmethod
    def _extract_body(cls, payload: Dict[str, Any]) -> str:
        """
        Recursively searches the payload for a text/plain part.
        Falls back to text/html if plain text isn't available.
        """
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return cls._decode_base64(part['body'].get('data', ''))
            
            # If no plain text, look deeper or grab html
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    return cls._decode_base64(part['body'].get('data', ''))
                elif 'parts' in part:
                    body = cls._extract_body(part)
                    if body:
                        return body
        elif payload.get('mimeType') == 'text/plain' or payload.get('mimeType') == 'text/html':
            return cls._decode_base64(payload['body'].get('data', ''))
        
        return ""

    @classmethod
    def parse(cls, raw_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the raw Gmail payload into a clean, normalized dictionary.
        """
        payload = raw_email.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        
        # Extract Body
        body = cls._extract_body(payload)
        
        # Check attachments (rough heuristic based on parts)
        has_attachments = any(
            part.get('filename') for part in payload.get('parts', []) if part.get('filename')
        )

        return {
            "gmail_message_id": raw_email['id'],
            "gmail_thread_id": raw_email['threadId'],
            "sender": sender,
            "subject": subject,
            "body": body.strip(),
            "has_attachments": has_attachments
        }
