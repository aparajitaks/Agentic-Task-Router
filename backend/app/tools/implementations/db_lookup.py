"""
app/tools/implementations/db_lookup.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Agents need context about past actions. A database lookup tool allows the AI
    to query recent tasks, system logs, or user history to make informed decisions.

WHAT IT DOES
    - Takes a natural language or structured query parameter.
    - Connects to PostgreSQL.
    - Retrieves recent `tasks` or `logs` and formats them as a readable string.
"""

from langchain_core.tools import tool
import asyncio
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.session import AsyncSessionLocal
from app.models.task import Task
from app.core.logging import get_logger

logger = get_logger(__name__)

async def _fetch_recent_tasks_async(limit: int) -> str:
    """Async helper to query DB."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(Task).order_by(desc(Task.created_at)).limit(limit)
            result = await db.execute(stmt)
            tasks = result.scalars().all()
            
            if not tasks:
                return "No recent tasks found."
                
            formatted = []
            for t in tasks:
                formatted.append(f"Task ID: {t.id} | Status: {t.status} | Title: {t.title}")
            return "\n".join(formatted)
    except Exception as e:
        logger.error(f"DB Lookup Error: {e}")
        return f"Failed to retrieve tasks: {str(e)}"

@tool
def db_lookup_tool(limit: int = 5) -> str:
    """
    Looks up the most recent tasks in the database to understand system history.
    Use this to verify if similar tasks were recently processed.
    Inputs required:
    - limit: The maximum number of recent tasks to retrieve (e.g., 5).
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_fetch_recent_tasks_async(limit))
    finally:
        loop.close()
