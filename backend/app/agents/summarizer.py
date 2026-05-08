"""
app/agents/summarizer.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Specialized agents perform one task very well. This is our Summarizer Agent.

WHAT IT DOES
    Takes the raw input text from the workflow state and generates a summary.
    Updates the `final_output` in the state.

HOW IT CONNECTS
    Called by the LangGraph workflow if the router decides on `summarizer_agent`.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.ai_services.llm_provider import get_llm
from app.prompts.agent_prompts import SUMMARIZER_SYSTEM_PROMPT
from app.state.workflow_state import WorkflowState


def summarize_task(state: WorkflowState) -> WorkflowState:
    """
    Summarizer Agent Node Function.
    """
    llm = get_llm(temperature=0.3)  # Slight creativity for better summaries
    
    messages = [
        SystemMessage(content=SUMMARIZER_SYSTEM_PROMPT),
        HumanMessage(content=f"Please summarize this:\n{state['input_text']}")
    ]
    
    try:
        response = llm.invoke(messages)
        
        # Update state with the result
        state["final_output"] = response.content
        state["current_status"] = "Summarization Complete"
        
    except Exception as e:
        state["error_message"] = f"Summarizer failed: {str(e)}"
        state["current_status"] = "Execution Failed"
        
    return state
