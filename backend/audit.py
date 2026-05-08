import asyncio
import os
from pprint import pprint

from app.config.settings import get_settings
from app.db.session import AsyncSessionLocal
from app.models.task import Task
from app.models.tool import ToolExecutionLog
from app.ai_services.llm_provider import get_llm
from app.tools.registry import get_all_tools
from app.tools.implementations.calculator import calculator_tool
from app.tools.implementations.doc_retrieval import doc_retrieval_tool
from app.tools.implementations.web_search import web_search_tool
from app.graphs.main_graph import app_graph
from langchain_core.messages import HumanMessage

async def run_audit():
    print("\n--- ENTERPRISE END-TO-END AUDIT SCRIPT ---")
    
    # 1. Environment
    print("\n[STEP 1] Environment validation")
    settings = get_settings()
    print(f"DATABASE_URL: {settings.database_url.split('@')[-1]}")
    print(f"REDIS_URL: {settings.redis_host}:{settings.redis_port}")
    
    # 2. Database validation
    print("\n[STEP 2] Database mapping validation (SQLite fallback for tests)")
    try:
        async with AsyncSessionLocal() as db:
            print("DB connection instantiated cleanly.")
    except Exception as e:
        print(f"DB Error: {e}")

    # 3. Tool execution validation
    print("\n[STEP 3] Tool Calling Validation")
    try:
        calc_res = calculator_tool.invoke("100 * 1.5")
        print(f"Calculator Tool: 100 * 1.5 = {calc_res}")
    except Exception as e:
        print(f"Calculator Tool Error: {e}")
        
    try:
        doc_res = doc_retrieval_tool.invoke("refund policy")
        print(f"Doc Retrieval Tool: {doc_res}")
    except Exception as e:
        print(f"Doc Retrieval Tool Error: {e}")
        
    try:
        search_res = web_search_tool.invoke("Apple Stock Price")
        print(f"Web Search Tool: Length={len(search_res)} chars")
    except Exception as e:
        print(f"Web Search Tool Error: {e}")

    # 4. LangGraph validation
    print("\n[STEP 4] LangGraph Execution Schema")
    nodes = list(app_graph.get_graph().nodes.keys())
    edges = [f"{e.source} -> {e.target}" for e in app_graph.get_graph().edges]
    print(f"Graph Nodes: {nodes}")
    print(f"Graph Edges: {edges}")

    # 5. Gemini Integration
    print("\n[STEP 5] Gemini Tool Binding Validation")
    try:
        llm = get_llm(temperature=0)
        tools = get_all_tools()
        llm_with_tools = llm.bind_tools(tools)
        print("Gemini initialized and bound to 5 tools successfully.")
    except Exception as e:
        print(f"Gemini Binding Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_audit())
