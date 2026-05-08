# app/models/__init__.py
# Import all models here so Alembic can discover them via Base.metadata
# when it imports this package.

from app.models.task import Task, TaskStatus
from app.models.agent import Agent, AgentType
from app.models.log import Log, LogLevel
from app.models.gmail import OAuthToken, EmailThread, EmailMessage, IngestionLog
from app.models.tool import ToolExecutionLog
from app.models.approval import Approval, ApprovalStatus, ApprovalPolicy
from app.models.user import User

__all__ = [
    "Task",
    "TaskStatus",
    "Agent",
    "AgentType",
    "Log",
    "LogLevel",
    "OAuthToken",
    "EmailThread",
    "EmailMessage",
    "IngestionLog",
    "ToolExecutionLog",
    "Approval",
    "ApprovalStatus",
    "ApprovalPolicy",
    "User",
]
