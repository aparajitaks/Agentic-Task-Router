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
from app.tools.registry import get_all_tools

def summarize_task(state: WorkflowState) -> dict:
    """
    Summarizer Agent Node Function.
    Now equipped with tool calling capabilities!
    """
    llm = get_llm(temperature=0.0)
    
    # Bind tools to the LLM
    tools = get_all_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Initialize messages if empty
    messages = state.get("messages", [])
    if not messages:
        messages = [
            SystemMessage(content=SUMMARIZER_SYSTEM_PROMPT),
            HumanMessage(content=f"Please summarize this input:\n{state.get('input_text', '')}")
        ]
        
    try:
        # Invoke the LLM with user_id in metadata for tool execution
        response = llm_with_tools.invoke(
            messages,
            config={"metadata": {"user_id": state.get("user_id")}}
        )
        
        return {
            "messages": [response],
            "final_output": response.content,
            "current_status": "Summarization Complete",
            "selected_agent": "summarizer_agent"
        }
        
    except Exception as e:
        return {
            "error_message": f"Summarizer failed: {str(e)}",
            "current_status": "Execution Failed"
        }
