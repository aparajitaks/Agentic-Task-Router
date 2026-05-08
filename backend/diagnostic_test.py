import asyncio
from app.config.settings import get_settings
from app.ai_services.llm_provider import get_llm
from langchain_core.messages import HumanMessage

async def test_gemini():
    try:
        settings = get_settings()
        print(f"Loaded Settings. Gemini Key length: {len(settings.gemini_api_key) if settings.gemini_api_key else 0}")
        
        llm = get_llm(temperature=0.0)
        messages = [HumanMessage(content="Hello! Reply with exactly 'System Check: OK'.")]
        
        print("Invoking Gemini...")
        response = llm.invoke(messages)
        print(f"Gemini Response: {response.content}")
        return True
    except Exception as e:
        print(f"Gemini test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_gemini())
