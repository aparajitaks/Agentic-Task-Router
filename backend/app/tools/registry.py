"""
app/tools/registry.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    In an enterprise agentic system, you don't want to hardcode tools into every
    agent. A central registry allows us to dynamically load, enable, and disable
    tools without altering the agent's core reasoning loops.

WHAT IT DOES
    - Holds a dictionary mapping tool names to actual LangChain Tool instances.
    - Provides a `get_all_tools()` method.
    - Enables future RBAC (Role-Based Access Control) where an agent only
      receives tools the user has permission to use.

HOW IT CONNECTS
    The LangGraph workflow and LangChain LLMs will import `get_all_tools()` and
    bind them via `llm.bind_tools(tools)`.
"""

from typing import List
from langchain_core.tools import BaseTool

# We will lazily load tool implementations to avoid circular imports.
_TOOL_REGISTRY: List[BaseTool] = []
_INITIALIZED = False

def init_registry():
    """Initializes and registers all tools."""
    global _TOOL_REGISTRY, _INITIALIZED
    if _INITIALIZED:
        return

    from app.tools.implementations.web_search import web_search_tool
    from app.tools.implementations.calculator import calculator_tool
    from app.tools.implementations.gmail_send import gmail_send_tool
    from app.tools.implementations.db_lookup import db_lookup_tool
    from app.tools.implementations.doc_retrieval import doc_retrieval_tool

    _TOOL_REGISTRY = [
        web_search_tool,
        calculator_tool,
        gmail_send_tool,
        db_lookup_tool,
        doc_retrieval_tool,
    ]
    _INITIALIZED = True

def get_all_tools() -> List[BaseTool]:
    """Returns a list of all active tools available to the agents."""
    if not _INITIALIZED:
        init_registry()
    return _TOOL_REGISTRY
