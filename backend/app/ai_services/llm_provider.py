"""
app/ai_services/llm_provider.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Hardcoding LLM providers (like OpenAI or Gemini) throughout the codebase
    causes vendor lock-in. This file acts as an abstraction layer (Factory Pattern).

WHAT IT DOES
    - Exposes a `get_llm()` factory function.
    - Can dynamically return `ChatOpenAI`, `ChatGoogleGenerativeAI`, or others
      based on environment variables or parameters.
    - Centralizes LLM configuration (temperature, keys, models).

HOW IT CONNECTS
    Agents (`app/agents/`) call `get_llm(temperature=0.7)` instead of instantiating
    `ChatOpenAI` directly. If we want to switch entirely to Gemini, we just change
    one line here, and all agents immediately use Gemini.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from pydantic import SecretStr
from app.config.settings import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Switch this to change the default provider across the entire system.
# Options: "gemini", "openai", "groq"
def get_llm(
    temperature: float = 0.0, 
    provider: str | None = None,
    model_name: str | None = None
) -> BaseChatModel:
    """
    Returns an instantiated LangChain ChatModel from the specified provider.
    If provider is not specified, uses the one from settings.
    """
    selected_provider = provider or settings.llm_provider
    selected_provider = selected_provider.lower()

    if selected_provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set but 'groq' is the selected provider.")
            
        model = model_name or settings.groq_model_name
        return ChatGroq(
            model=model,
            api_key=SecretStr(settings.groq_api_key),
            temperature=temperature,
        )

    elif selected_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set but 'gemini' is the selected provider.")
            
        model = model_name or settings.gemini_model_name
        return ChatGoogleGenerativeAI(
            model=model,
            api_key=SecretStr(settings.gemini_api_key),
            temperature=temperature,
        )
        
    elif selected_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set but 'openai' is the selected provider.")
            
        model = model_name or settings.openai_model_name
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(settings.openai_api_key),
            temperature=temperature,
        )
        
    else:
        raise ValueError(f"Unsupported LLM provider: {selected_provider}")
