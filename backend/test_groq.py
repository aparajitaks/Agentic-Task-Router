import asyncio
from app.ai_services.llm_provider import get_llm
from langchain_core.messages import HumanMessage

async def main():
    try:
        # Default is now Groq
        llm = get_llm(temperature=0.0)
        print("Using LLM:", type(llm).__name__)
        
        response = llm.invoke([HumanMessage(content="Hello! Please reply with 'Groq is working perfectly!'")])
        print("Response:", response.content)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
