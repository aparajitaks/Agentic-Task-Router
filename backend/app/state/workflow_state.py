"""
app/state/workflow_state.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    LangGraph relies on a "State" object that gets passed between nodes in
    the graph. Each node can read this state and update it.

WHAT IT DOES
    Defines the `WorkflowState` TypedDict. This acts as the memory for
    a single execution of our agentic workflow.

HOW IT CONNECTS
    Used by `app/graphs/main_graph.py` to define the graph's StateSchema.
    Read/Updated by every agent in `app/agents/`.
"""

from typing import TypedDict, Optional, Any, Annotated
from langgraph.graph.message import add_messages

class WorkflowState(TypedDict):
    """
    Represents the state of the agentic workflow at any given time.
    
    Fields:
    - task_id: UUID of the task in the database.
    - input_text: The raw request from the user.
    - route: The decision made by the router agent (e.g., 'summarizer_agent').
    - selected_agent: The name of the agent currently executing.
    - current_status: Tracks workflow progress.
    - intermediate_steps: Stores intermediate thoughts or tool calls.
    - final_output: The final result to return to the user.
    - error_message: Holds error details if a node fails.
    - messages: LangGraph standard message array for ToolNode execution.
    """
    task_id: str
    user_id: str  # Critical for multi-tenant isolation in graph nodes
    input_text: str
    route: Optional[str]
    selected_agent: Optional[str]
    current_status: str
    intermediate_steps: list[dict[str, Any]]
    final_output: Optional[str]
    error_message: Optional[str]
    messages: Annotated[list, add_messages]
