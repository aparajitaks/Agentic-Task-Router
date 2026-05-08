"""
app/routes/tools.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Provides REST endpoints for inspecting and debugging the tool execution
    capabilities.

WHAT IT DOES
    - GET /api/v1/tools: Lists all available tools in the registry.
    - POST /api/v1/tools/execute: Manually trigger a specific tool for debugging.
    - GET /api/v1/tools/logs: Fetch historical tool execution logs.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.session import get_db
from app.models.tool import ToolExecutionLog
from app.tools.registry import get_all_tools

router = APIRouter(prefix="/tools", tags=["Tools"])

@router.get("", summary="List all registered tools")
async def list_tools():
    """Returns a list of all tools currently available to the AI agents."""
    tools = get_all_tools()
    return {
        "success": True,
        "data": [
            {
                "name": t.name,
                "description": t.description
            } for t in tools
        ]
    }

@router.get("/logs", summary="Get tool execution logs")
async def get_tool_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetches the recent history of tools executed by the AI."""
    stmt = select(ToolExecutionLog).order_by(desc(ToolExecutionLog.created_at)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return {
        "success": True,
        "data": [
            {
                "id": str(log.id),
                "task_id": str(log.task_id) if log.task_id else None,
                "tool_name": log.tool_name,
                "is_success": log.is_success,
                "execution_time_ms": log.execution_time_ms,
                "created_at": log.created_at.isoformat()
            } for log in logs
        ]
    }
