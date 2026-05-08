"""
app/tools/implementations/web_search.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    LLMs have a knowledge cutoff. A web search tool allows the agent to fetch
    real-time, up-to-date information directly from the internet.

WHAT IT DOES
    - Takes a search query string.
    - Uses DuckDuckGo search (no API key required) to fetch top results.
    - Returns a structured markdown summary of the results.
"""

from langchain_core.tools import tool
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper

@tool
def web_search_tool(query: str) -> str:
    """
    Executes a web search to find real-time information on the internet.
    Use this when you need up-to-date facts, news, or external context.
    """
    try:
        # Wrap the API safely
        wrapper = DuckDuckGoSearchAPIWrapper(max_results=3)
        search = DuckDuckGoSearchRun(api_wrapper=wrapper)
        
        result = search.invoke(query)
        
        if not result or result == "No good DuckDuckGo Search Result was found":
            return "No search results found. Try rephrasing the query."
            
        return f"Search Results for '{query}':\n\n{result}"
        
    except Exception as e:
        return f"Error executing web search: {str(e)}"
