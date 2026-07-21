import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from app.agent.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

def get_llm(temperature:float = 0.0)-> ChatOpenAI:
    """Returns an configurated instance of ChatOpeanAI ready to use"""
    
    # model_name = str(LLM_MODEL_NAME)
    # base_url = str(LLM_BASE_URL) if LLM_BASE_URL else None
    # raw_api_key = str(LLM_API_KEY) if LLM_API_KEY else "ollama"
    # api_key = SecretStr(raw_api_key)

    model_name = "google/gemma-4-26b-a4b-it:free"
    base_url = "https://openrouter.ai/api/v1"
    raw_api_key = "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"
    api_key = SecretStr(raw_api_key)


    try:
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature
        )
    except Exception as e:
        return ChatOpenAI()