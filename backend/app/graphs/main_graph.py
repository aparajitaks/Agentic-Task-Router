"""
app/graphs/main_graph.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This is where LangGraph orchestrates the entire agentic workflow, now
    empowered with autonomous Tool execution.

WHAT IT DOES
    - Defines nodes for agents and tools.
    - Uses `tools_condition` to route to the ToolNode if an agent requested an action.
    - Routes the output of tools back to the agent that requested them for reasoning.
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.state.workflow_state import WorkflowState
from app.agents.router import route_task
from app.agents.summarizer import summarize_task
from app.agents.reply_generator import generate_reply_task
from app.tools.registry import get_all_tools


def route_after_agent(state: WorkflowState) -> Literal["tools", "__end__"]:
    """
    Checks if the last message from the agent contains a tool call.
    If yes, route to the ToolNode. If no, we are done (END).
    """
    return tools_condition(state) # type: ignore


def route_after_tools(state: WorkflowState) -> str:
    """
    After tools finish, we must return control to the agent that called them
    so it can reason over the tool output.
    """
    selected = state.get("selected_agent")
    if selected in ["summarizer_agent", "reply_generator_agent"]:
        return selected
    return END

def build_graph():
    """
    Constructs and compiles the LangGraph workflow with tool capabilities.
    """
    workflow = StateGraph(WorkflowState)

    # 1. Add Nodes
    workflow.add_node("router", route_task)
    workflow.add_node("summarizer_agent", summarize_task)
    workflow.add_node("reply_generator_agent", generate_reply_task)
    
    # 2. Add the dynamic Tool Execution Node
    # ToolNode automatically executes the tools requested in the last AIMessage
    workflow.add_node("tools", ToolNode(get_all_tools()))

    # 3. Define the Entry Point
    workflow.add_edge(START, "router")

    # 4. Define Router Edges
    def route_condition(state: WorkflowState) -> Literal["summarizer_agent", "reply_generator_agent", "unknown"]:
        route = state.get("route")
        if not route or route not in ["summarizer_agent", "reply_generator_agent"]:
            return "unknown"
        return route # type: ignore

    workflow.add_conditional_edges(
        "router",
        route_condition,
        {
            "summarizer_agent": "summarizer_agent",
            "reply_generator_agent": "reply_generator_agent",
            "unknown": END
        }
    )

    # 5. Define Agent-to-Tool Edges (The ReAct Loop)
    workflow.add_conditional_edges(
        "summarizer_agent",
        route_after_agent,
        {"tools": "tools", "__end__": END}
    )
    workflow.add_conditional_edges(
        "reply_generator_agent",
        route_after_agent,
        {"tools": "tools", "__end__": END}
    )

    # 6. Define Tool-to-Agent Edges (Loop back to reason over results)
    workflow.add_conditional_edges(
        "tools",
        route_after_tools
    )

    # Compile into a runnable application
    return workflow.compile()

# Compile the graph once when the module loads
app_graph = build_graph()
