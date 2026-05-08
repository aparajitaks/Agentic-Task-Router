"""
app/ai_services/llm.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Centralizes the initialization of our Large Language Models (LLMs).
    If we ever want to switch from OpenAI to Anthropic, or change the
    model temperature globally, we do it in one place.

WHAT IT DOES
    Provides a configured instance of ChatOpenAI using credentials
    from our settings.

HOW IT CONNECTS
    Imported by agents (`summarizer.py`, `reply_generator.py`, `router.py`)
    to execute prompts against the LLM.
"""

from langchain_openai import ChatOpenAI

from app.config.settings import get_settings

settings = get_settings()

def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """
    Returns a configured instance of ChatOpenAI.
    
    Args:
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative).
                     Default is 0.0 for reliable agent behavior.
    """
    if not settings.openai_api_key or "placeholder" in settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set or is a placeholder in .env")

    return ChatOpenAI(
        model=settings.openai_model_name,
        api_key=settings.openai_api_key,
        temperature=temperature,
    )
