# app/agent/config.py
import os
from dotenv import load_dotenv
from pydantic import SecretStr

LLM_API_KEY = SecretStr(str(os.getenv("LLM_API_KEY")))
LLM_BASE_URL = os.getenv("LLM_BASE_URL") 
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME") 
MAX_TOOLS_PER_STEP = 3
MAX_DRAFT_PER_STEP = 5