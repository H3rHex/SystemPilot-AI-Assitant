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

    model_name = "llama3.2:latest"
    base_url = "http://localhost:11434/v1"
    raw_api_key = "ollama"
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