import os

from typing import cast
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.llm import get_llm

class PlannerOutput(BaseModel):
    needs_tool:bool = Field(
        description="True if the request requires inspecting, executing, or checking the OS/local system state. False for general conversation or theoretical questions."
    )

    reasoning:str = Field(
        description="Short reasoning explaining why a tool is needed or not."
    )

llm = get_llm(0.0)
structured_llm = llm.with_structured_output(PlannerOutput)

SYSTEM_PROMPT = """You are the intent classifier for SystemPilot.

Your sole task is to decide whether the user's input can be answered directly using general knowledge and conversation, or if it requires invoking an external tool.

- Set `needs_tool` to True if the request involves executing system commands, reading local environment state, performing mathematical calculations, or any task requiring precise tool assistance.
- Set `needs_tool` to False ONLY if the request can be completely and accurately answered through standard reasoning, general knowledge, or casual conversation."""

def planner_node(state: AgentState) -> dict:
    """Planner Node: Evaluates user input and decides whether tools are required."""
    user_input = state["input"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    response = cast(PlannerOutput, structured_llm.invoke(messages))    
    
    return {
        "needs_tool": response.needs_tool
    }