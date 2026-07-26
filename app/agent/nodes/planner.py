import os

from typing import cast
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.observability import observe
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

SYSTEM_PROMPT = """Analyze the user request and decide if executing a tool or interacting with the system/environment is required.

Set needs_tool = True IF:
- The request asks about system capabilities, available tools, or help (e.g., "What can you do?", "What tools do you have?", "Help").
- The request requires reading, writing, searching, modifying, or deleting local files, system resources, or state.
- The request asks to execute system commands, code, scripts, or external API calls.
- The request involves checking hardware, system status, processes, or dynamic local data.

Set needs_tool = False STRICTLY ONLY IF:
- Pure conceptual explanations, theories, or general knowledge (e.g., "What is Linux?", "Explain Python").
- Generating code snippets in text without requesting to run or save them to disk.
- Casual greetings (e.g., "Hello", "How are you?") without asking about capabilities.

WHEN IN DOUBT -> ALWAYS SET needs_tool = True.
"""

@observe(name="planner_node", as_type="chain")
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