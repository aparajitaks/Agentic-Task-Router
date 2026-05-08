"""
app/tools/implementations/doc_retrieval.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    This provides the foundation for RAG (Retrieval-Augmented Generation).
    Agents use this tool to search internal knowledge bases, policies, or
    SOPs (Standard Operating Procedures) before taking action.

WHAT IT DOES
    - Takes a search query.
    - In a full system, this would embed the query and search pgvector.
    - For now, it provides a mocked static knowledge base search to demonstrate
      the capability without needing a complex embedding infrastructure.
"""

from langchain_core.tools import tool
from typing import Dict

# Mock Knowledge Base (In Level 4 we replace this with pgvector + embeddings)
_KNOWLEDGE_BASE: Dict[str, str] = {
    "refund policy": "Refunds are allowed within 30 days of purchase if the item is unused.",
    "support hours": "Our support team is available Monday to Friday, 9 AM to 5 PM EST.",
    "escalation": "If a customer is angry, apologize immediately and route the task to a human agent.",
}

@tool
def doc_retrieval_tool(query: str) -> str:
    """
    Searches the internal company knowledge base for policy documents, rules, and SOPs.
    Use this when you need to know company rules or policies to answer a question.
    """
    query = query.lower()
    
    # Simple keyword matching for the mock KB
    for key, doc in _KNOWLEDGE_BASE.items():
        if key in query:
            return f"Found relevant document:\n\n{doc}"
            
    return "No relevant internal documents found for that query."
