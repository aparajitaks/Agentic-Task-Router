"""
app/ingestion/email_ingester.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This is the orchestration layer for the "Real-World Integration". It connects
    the Gmail API, the Email Parser, the Database, and the Celery Queue.

WHAT IT DOES
    - Polls unread emails via `GmailClient`.
    - Parses them via `EmailParser`.
    - Saves the emails to the `email_messages` table.
    - Generates a `Task` in the DB for the LangGraph agents.
    - Pushes the task into the Celery Queue (`execute_agentic_workflow_task.delay`).
    - Marks the email as read so it isn't processed again.

HOW IT CONNECTS
    Triggered manually by an API endpoint (`/api/v1/gmail/sync`) or automatically
    by a scheduled Celery Beat task (polling).
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.oauth.google import GoogleOAuthService
from app.gmail.client import GmailClient
from app.parsers.email_parser import EmailParser
from app.models.gmail import EmailMessage, EmailThread, IngestionLog
from app.models.task import Task, TaskStatus
from app.workers.tasks import execute_agentic_workflow_task
from app.core.logging import get_logger

logger = get_logger(__name__)

class EmailIngester:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id
        self.oauth_service = GoogleOAuthService()

    async def sync_unread_emails(self) -> int:
        """
        Main pipeline: Fetches unread emails, parses them, creates tasks, and queues them.
        Returns the number of emails processed.
        """
        # 1. Authenticate
        creds = await self.oauth_service.get_valid_credentials(self.db, self.user_id)
        client = GmailClient(credentials=creds)

        # 2. Fetch Unread Email IDs
        try:
            unread_metadata = client.fetch_unread_emails(max_results=20)
        except Exception as e:
            await self._log_ingestion("FAILED", error=str(e))
            raise

        if not unread_metadata:
            await self._log_ingestion("SUCCESS", count=0)
            return 0

        processed_count = 0

        # 3. Process each email
        for meta in unread_metadata:
            msg_id = meta['id']
            
            # Check if we already processed this message for this user
            existing = await self.db.execute(
                select(EmailMessage).where(
                    EmailMessage.gmail_message_id == msg_id,
                    EmailMessage.user_id == self.user_id
                )
            )
            if existing.scalar_one_or_none():
                # Already processed, just remove UNREAD label to clear inbox
                client.mark_as_read(msg_id)
                continue

            try:
                # Download full payload & Parse
                raw_email = client.get_email_details(msg_id)
                parsed = EmailParser.parse(raw_email)

                # 4. Save Thread (if new)
                thread = await self._get_or_create_thread(parsed['gmail_thread_id'], parsed['subject'])

                # 5. Create AI Task
                # The agent input is the email body and subject
                input_text = f"Email Subject: {parsed['subject']}\n\nEmail Body:\n{parsed['body']}"
                
                task = Task(
                    title=f"Email from {parsed['sender']}",
                    description="Automatically generated from Gmail Integration",
                    input_text=input_text,
                    status=TaskStatus.QUEUED,
                    user_id=self.user_id
                )
                self.db.add(task)
                await self.db.flush() # Get task ID

                # 6. Save Email Message
                email_msg = EmailMessage(
                    gmail_message_id=parsed['gmail_message_id'],
                    user_id=self.user_id,
                    thread_id=thread.id,
                    sender_email=parsed['sender'],
                    subject=parsed['subject'],
                    body_plain=parsed['body'],
                    has_attachments=parsed['has_attachments'],
                    received_at=datetime.now(timezone.utc),
                    status="QUEUED",
                    task_id=task.id
                )
                self.db.add(email_msg)

                # 7. Queue to Celery
                execute_agentic_workflow_task.delay(str(task.id))

                # 8. Mark Read in Gmail
                client.mark_as_read(msg_id)
                processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process email {msg_id}: {str(e)}")
                continue

        await self.db.commit()
        await self._log_ingestion("SUCCESS", count=processed_count)
        return processed_count

    async def _get_or_create_thread(self, thread_id: str, subject: str) -> EmailThread:
        stmt = select(EmailThread).where(EmailThread.gmail_thread_id == thread_id)
        result = await self.db.execute(stmt)
        thread = result.scalar_one_or_none()
        if not thread:
            thread = EmailThread(gmail_thread_id=thread_id, subject=subject)
            self.db.add(thread)
            await self.db.flush()
        return thread

    async def _log_ingestion(self, status: str, count: int = 0, error: str = None) -> None:
        log = IngestionLog(
            status=status,
            emails_fetched=count,
            error_message=error
        )
        self.db.add(log)
        await self.db.commit()
