"""
app/agents/reply_generator.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Specialized agent for drafting professional replies to messages or emails.

WHAT IT DOES
    Reads the input text and generates a draft reply.

HOW IT CONNECTS
    Called by the LangGraph workflow if the router decides on `reply_generator_agent`.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.ai_services.llm import get_llm
from app.prompts.agent_prompts import REPLY_GENERATOR_SYSTEM_PROMPT
from app.state.workflow_state import WorkflowState


def generate_reply_task(state: WorkflowState) -> WorkflowState:
    """
    Reply Generator Agent Node Function.
    """
    llm = get_llm(temperature=0.5)  # Higher temperature for more natural language
    
    messages = [
        SystemMessage(content=REPLY_GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Please draft a reply to this:\n{state['input_text']}")
    ]
    
    try:
        response = llm.invoke(messages)
        
        # Update state with the result
        state["final_output"] = response.content
        state["current_status"] = "Reply Generation Complete"
        
    except Exception as e:
        state["error_message"] = f"Reply Generator failed: {str(e)}"
        state["current_status"] = "Execution Failed"
        
    return state
