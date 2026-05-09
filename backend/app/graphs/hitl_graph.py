"""
app/graphs/hitl_graph.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The original `main_graph.py` runs autonomously to completion. This file
    extends that architecture with a HITL-aware graph that pauses execution
    before sending any email output, requiring human sign-off first.

    This is the architectural core of enterprise AI governance: the agent
    proposes, the human disposes.

WHAT IT DOES
    Adds a `human_review_node` into the LangGraph workflow:

    START → router → [summarizer|reply_generator] → tools (loop) →
    human_review_node → PAUSE (creates DB checkpoint) → END

    After a human approves via API, `app/workers/resume.py` takes the
    persisted checkpoint and drives the workflow to COMPLETED.

    The graph uses an `interrupt_before` compile option on the node that
    would send email, ensuring the human always sees it first.

HOW IT CONNECTS
    - app/state/workflow_state.py  → WorkflowState with new HITL fields
    - app/services/approval.py     → `create_approval()` called inside node
    - app/workers/resume.py        → Resumes after human decision
    - app/execution_engine/engine.py → Selects HITL vs autonomous graph
"""

import asyncio
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import messages_to_dict

from app.state.workflow_state import WorkflowState
from app.agents.router import route_task
from app.agents.summarizer import summarize_task
from app.agents.reply_generator import generate_reply_task
from app.tools.registry import get_all_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


def route_after_agent(state: WorkflowState) -> Literal["tools", "__end__"]:
    """Routes to tools if the agent requested an action, else ends."""
    return tools_condition(state)  # type: ignore


def route_after_tools(state: WorkflowState) -> str:
    """Returns control to the agent that called the tools for further reasoning."""
    selected = state.get("selected_agent")
    if selected in ["summarizer_agent", "reply_generator_agent"]:
        return selected
    return END

def send_email_node(state: WorkflowState) -> WorkflowState:
    """
    Downstream node that executes AFTER human approval.
    In a real app, this would use Gmail API to actually send the drafted reply.
    """
    logger.info(f"Executing send_email_node for task: {state.get('task_id')}")
    # Here we would actually dispatch the email using `state.get("final_output")`
    return state


def human_review_node(state: WorkflowState) -> WorkflowState:
    """
    The HITL checkpoint node. This node:
    1. Extracts the AI's draft output from state.
    2. Serializes the full WorkflowState as a checkpoint.
    3. Calls `create_approval()` to persist the checkpoint and pause the task.
    4. Returns state with `current_status` set to `AWAITING_APPROVAL`.

    The graph then ends. The Celery task that called `astream()` sees the
    workflow complete, but the Task DB record is in AWAITING_APPROVAL state.
    Resumption happens via a NEW Celery task triggered by the approval API.

    NOTE: This is synchronous because LangGraph nodes are sync by default.
    We run the async service in a new event loop.
    """
    task_id_str = state.get("task_id")
    final_output = state.get("final_output") or ""
    input_text = state.get("input_text") or ""
    route = state.get("route") or "unknown"
    selected_agent = state.get("selected_agent") or "unknown"
    user_id_str = state.get("user_id")

    if not task_id_str:
        logger.error("human_review_node: task_id missing from state — cannot create approval")
        return {**state, "current_status": "error", "error_message": "No task_id in state"}

    logger.info("HITL checkpoint reached | task_id=%s agent=%s", task_id_str, selected_agent)

    # Serialize the current state as the graph checkpoint
    # We now correctly serialize LangChain messages to preserve agent memory
    checkpoint = {
        "task_id": task_id_str,
        "input_text": input_text,
        "route": route,
        "selected_agent": selected_agent,
        "final_output": final_output,
        "intermediate_steps": state.get("intermediate_steps", []),
        "current_status": "AWAITING_APPROVAL",
        "error_message": state.get("error_message"),
        "messages": messages_to_dict(state.get("messages", [])),
    }

    workflow_context = {
        "route": route,
        "selected_agent": selected_agent,
        "tool_calls_count": len(state.get("intermediate_steps", [])),
    }

    # Run async approval creation in a synchronous context
    loop = asyncio.new_event_loop()
    try:
        from app.db.session import AsyncSessionLocal
        from app.services.approval import create_approval
        import uuid

        async def _create():
            async with AsyncSessionLocal() as db:
                return await create_approval(
                    db,
                    task_id=uuid.UUID(task_id_str),
                    user_id=uuid.UUID(user_id_str) if user_id_str else None,
                    ai_generated_draft=final_output,
                    original_input=input_text,
                    graph_checkpoint_state=checkpoint,
                    checkpoint_node="human_review_node",
                    workflow_context=workflow_context,
                )

        approval = loop.run_until_complete(_create())
        logger.info("Approval checkpoint persisted | approval_id=%s", approval.id)

    except Exception as exc:
        logger.error("Failed to create approval checkpoint: %s", str(exc), exc_info=True)
        return {**state, "current_status": "error", "error_message": str(exc)}
    finally:
        loop.close()

    return {
        **state,
        "current_status": "AWAITING_APPROVAL",
    }


def should_require_human_review(state: WorkflowState) -> str:
    """
    Policy router: determines if the workflow needs human review.

    Current policy: ALWAYS require approval for reply_generator_agent output.
    Summarizer outputs are auto-approved (informational, no action taken).

    This is where you'd plug in the `ApprovalPolicy` engine for configurable rules.
    """
    selected_agent = state.get("selected_agent", "")
    if selected_agent == "reply_generator_agent":
        return "human_review"
    return "__end__"


def build_hitl_graph():
    """
    Builds the HITL-enabled LangGraph workflow.

    This graph is identical to the autonomous graph EXCEPT:
    - After the reply_generator_agent produces output, the flow is
      intercepted by `human_review_node` before ending.
    - The summarizer_agent bypasses review (it only summarizes, doesn't act).
    """
    workflow = StateGraph(WorkflowState)

    # ── Nodes ─────────────────────────────────────────────────────────────────
    workflow.add_node("router", route_task)
    workflow.add_node("summarizer_agent", summarize_task)
    workflow.add_node("reply_generator_agent", generate_reply_task)
    workflow.add_node("tools", ToolNode(get_all_tools()))
    workflow.add_node("human_review_node", human_review_node)
    workflow.add_node("send_email_node", send_email_node)

    # ── Entry Point ───────────────────────────────────────────────────────────
    workflow.add_edge(START, "router")

    # ── Router → Agent Edges ──────────────────────────────────────────────────
    def route_condition(state: WorkflowState) -> Literal["summarizer_agent", "reply_generator_agent", "unknown"]:
        route = state.get("route")
        if route not in ["summarizer_agent", "reply_generator_agent"]:
            return "unknown"
        return route  # type: ignore

    workflow.add_conditional_edges(
        "router",
        route_condition,
        {
            "summarizer_agent": "summarizer_agent",
            "reply_generator_agent": "reply_generator_agent",
            "unknown": END,
        }
    )

    # ── Agent → Tools (ReAct Loop) ────────────────────────────────────────────
    workflow.add_conditional_edges(
        "summarizer_agent",
        route_after_agent,
        {"tools": "tools", "__end__": END}
    )
    workflow.add_conditional_edges(
        "reply_generator_agent",
        route_after_agent,
        {"tools": "tools", "__end__": "human_review_node"}  # Always route to HITL
    )

    # ── Tools → Agent (loop back) ─────────────────────────────────────────────
    workflow.add_conditional_edges("tools", route_after_tools)

    # ── HITL → Downstream Nodes ───────────────────────────────────────────────
    workflow.add_edge("human_review_node", "send_email_node")
    workflow.add_edge("send_email_node", END)

    # Use MemorySaver as a transient checkpointer to enable interrupt_before
    # The actual persistence across Celery workers is handled by our DB checkpoints
    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["send_email_node"]
    )


# Module-level HITL graph instance
hitl_graph = build_hitl_graph()
