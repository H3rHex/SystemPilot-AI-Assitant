import os
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL")
LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
LLM_MODEL_NAME:str | None = os.getenv("LLM_MODEL_NAME")
LLM_STREAMING: bool = os.getenv("LLM_STREAMING", "false").lower() == "true"

SYSTEM_PROMPT:str = "You are SystemPilot, a native system copilot for SO. Keep responses concise, clear, and focused on technical accuracy."