import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from app.agent.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME, USE_LANGFUSE


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """Returns a configured instance of ChatOpenAI ready to use."""

    model_name = str(LLM_MODEL_NAME or "llama3.2:latest")
    base_url = str(LLM_BASE_URL or "http://localhost:11434/v1")
    raw_api_key = str(LLM_API_KEY or "ollama")
    api_key = SecretStr(raw_api_key)

    callbacks = []
    if USE_LANGFUSE:
        try:
            from langfuse.langchain import CallbackHandler
            callbacks.append(CallbackHandler())
        except Exception:
            callbacks = []

    try:
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            callbacks=callbacks or None,
        )
    except Exception:
        return ChatOpenAI()