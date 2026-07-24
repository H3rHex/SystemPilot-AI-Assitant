# app/agent/config.py
import os
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

LLM_API_KEY = SecretStr(str(os.getenv("LLM_API_KEY", "")))
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
USE_LANGFUSE = os.getenv("USE_LANGFUSE", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}