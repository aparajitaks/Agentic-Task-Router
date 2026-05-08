"""
app/graphs/main_graph.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This is where LangGraph orchestrates the entire agentic workflow.
    Instead of hardcoding "if statement -> call agent", we define a directed
    graph. This pattern scales gracefully when we add human-in-the-loop,
    retries, or dozens of specialized agents.

WHAT IT DOES
    Defines the nodes (agents) and edges (routing logic).
    Compiles the graph into an executable state machine.

HOW IT CONNECTS
    The orchestrator (`app/orchestrators/workflow_orchestrator.py`) calls
    `app_graph.invoke(initial_state)` to run a task.
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.state.workflow_state import WorkflowState
from app.agents.router import route_task
from app.agents.summarizer import summarize_task
from app.agents.reply_generator import generate_reply_task


def build_graph():
    """
    Constructs and compiles the LangGraph workflow.
    """
    # 1. Initialize the StateGraph with our TypedDict
    workflow = StateGraph(WorkflowState)

    # 2. Add Nodes (the actual functions/agents that will run)
    workflow.add_node("router", route_task)
    workflow.add_node("summarizer_agent", summarize_task)
    workflow.add_node("reply_generator_agent", generate_reply_task)

    # 3. Define the Entry Point
    workflow.add_edge(START, "router")

    # 4. Define Conditional Edges (Routing Logic)
    def route_condition(state: WorkflowState) -> Literal["summarizer_agent", "reply_generator_agent", "unknown"]:
        """
        Reads the state after the router node finishes.
        Returns the name of the next node to execute.
        """
        route = state.get("route")
        
        # If router failed or returned unknown, we end the graph.
        if not route or route not in ["summarizer_agent", "reply_generator_agent"]:
            return "unknown"
            
        return route # type: ignore

    # Add the conditional edges originating from the "router" node
    workflow.add_conditional_edges(
        "router",
        route_condition,
        {
            "summarizer_agent": "summarizer_agent",
            "reply_generator_agent": "reply_generator_agent",
            "unknown": END  # If unknown, just stop
        }
    )

    # 5. Define Exit Edges (agents -> END)
    workflow.add_edge("summarizer_agent", END)
    workflow.add_edge("reply_generator_agent", END)

    # 6. Compile into a runnable application
    return workflow.compile()

# Compile the graph once when the module loads
app_graph = build_graph()
