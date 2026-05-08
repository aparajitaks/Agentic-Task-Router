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

from app.ai_services.llm_provider import get_llm
from app.prompts.agent_prompts import REPLY_GENERATOR_SYSTEM_PROMPT
from app.state.workflow_state import WorkflowState


from langchain_core.messages import SystemMessage, HumanMessage
from app.tools.registry import get_all_tools

def generate_reply_task(state: WorkflowState) -> dict:
    """
    Reply Generator Agent Node Function.
    Now equipped with tool calling!
    """
    llm = get_llm(temperature=0.0)
    
    # Bind the tools from the registry to the LLM
    tools = get_all_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Initialize messages if empty
    messages = state.get("messages", [])
    if not messages:
        messages = [
            SystemMessage(content=REPLY_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=f"Please process this request:\n{state.get('input_text', '')}")
        ]
    
    try:
        # Invoke the LLM with user_id in metadata for tool execution
        response = llm_with_tools.invoke(
            messages,
            config={"metadata": {"user_id": state.get("user_id")}}
        )
        
        # We return a dict that LangGraph will use to update the state
        # The 'messages' key tells LangGraph to append this response to the history
        return {
            "messages": [response],
            "final_output": response.content,
            "current_status": "Reply Generation Complete",
            "selected_agent": "reply_generator_agent"
        }
        
    except Exception as e:
        return {
            "error_message": f"Reply Generator failed: {str(e)}",
            "current_status": "Execution Failed"
        }
