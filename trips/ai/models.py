import os
from langchain_openai import ChatOpenAI


def get_llm(model: str = "gpt-4o", temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
