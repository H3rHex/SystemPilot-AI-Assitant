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

SYSTEM_PROMPT = """Classify if the request needs system tools/local access.

needs_tool = False: greetings, general knowledge.
needs_tool = True: local files, system status, IP, RAM, CPU, disk, commands.

If unsure -> needs_tool = True.

Examples:
"Hola" -> False
"What is Linux?" -> False
"Check my disk space" -> True
"List files" -> True
"What is my IP?" -> True"""

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