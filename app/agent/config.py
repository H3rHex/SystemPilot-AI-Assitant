# app/agent/config.py
import os
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

raw_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama"

LLM_API_KEY = SecretStr(raw_api_key)
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME") or os.getenv("MODEL_NAME") or "gpt-4o-mini"
MAX_TOOLS_PER_STEP = 3