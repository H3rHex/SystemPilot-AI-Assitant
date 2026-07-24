import os

from typing import cast
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.llm import get_llm

class PlannerOutput(BaseModel):
    needs_tool: bool = Field(
        description=(
            "True if the request requires system status (OS, RAM, CPU, Disk, IP), "
            "executing shell commands, file system actions, or solving math/calculations. "
            "False ONLY for general chat, text explanations, or theoretical answers."
        )
    )

    reasoning: str = Field(
        description="One short sentence in English explaining why a tool is or isn't required."
    )

llm = get_llm(0.0)
structured_llm = llm.with_structured_output(PlannerOutput)

SYSTEM_PROMPT = """Analyze if the user request requires executing a tool, inspecting local system state, or performing calculations.

CRITICAL RULE:
Any question asking about "my system", "my OS", "my computer", "my PC", or current hardware status refers to LOCAL HARDWARE DATA and MUST use a tool.

needs_tool = True:
- Queries asking about "my OS", "my system", OS name/version, RAM, CPU, disk, IP, hostname, processes, or local files.
- Command Execution: Requests to run, create, write, modify, or delete anything on the local machine.
- Math & Calculations: Any math problem or arithmetic (do NOT calculate manually).

needs_tool = False:
- General theory, definitions (e.g., "What is Linux?"), code writing without execution, or conversational chat.

If unsure -> needs_tool = True.
"""

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