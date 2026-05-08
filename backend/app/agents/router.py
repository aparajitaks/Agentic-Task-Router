"""
app/agents/router.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    The Router is the brain of the agentic system. It decides which specialized
    agent should handle the user's request. This prevents a single "god prompt"
    and allows the system to scale to dozens of specialized agents.

WHAT IT DOES
    Uses LangChain's structured output feature (with Pydantic) to force the LLM
    to return a valid JSON object containing exactly one key: `route`.

HOW IT CONNECTS
    Called by the LangGraph workflow (`main_graph.py`) as the very first node.
"""

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai_services.llm_provider import get_llm
from app.prompts.agent_prompts import ROUTER_SYSTEM_PROMPT
from app.state.workflow_state import WorkflowState


class RouteDecision(BaseModel):
    """Schema forcing the LLM to output a structured routing decision."""
    route: Literal["summarizer_agent", "reply_generator_agent", "unknown"] = Field(
        ...,
        description="The chosen agent route based on the input text."
    )


def route_task(state: WorkflowState) -> WorkflowState:
    """
    Router Agent Node Function.
    Reads the input_text from state, prompts the LLM to decide the route,
    and updates the state with the decision.
    """
    llm = get_llm(temperature=0.0)
    
    # Bind the Pydantic schema to force structured JSON output
    structured_llm = llm.with_structured_output(RouteDecision)
    
    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=f"INPUT TEXT:\n{state['input_text']}")
    ]
    
    from typing import Literal, cast
    
    try:
        # Invoke the LLM; it returns a RouteDecision Pydantic object
        decision = cast(RouteDecision, structured_llm.invoke(messages))
        
        # Update state
        state["route"] = decision.route
        state["current_status"] = f"Routed to {decision.route}"
        state["selected_agent"] = decision.route
        
    except Exception as e:
        state["route"] = "unknown"
        state["error_message"] = f"Router failed: {str(e)}"
        state["current_status"] = "Routing Failed"
        
    return state
