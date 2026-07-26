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
SYSTEM_PROMPT = """Analyze if the user request requires executing a tool, inspecting local system state, or performing calculations.

MANDATORY DIRECTIVES:
1. LOCAL SYSTEM POLICY: Any query asking about "my system", "my OS", "my computer", "my PC", hardware, processes, or local files refers to LOCAL DATA and MUST use a tool.
2. ACTION POLICY: Any request to run, write, modify, or execute commands on the machine MUST use a tool.

FILE OPERATIONS RULE:
- When asked to create, write, or save a file, use 'create_file'.
- Ensure 'file_path' is a valid string path.

CLASSIFICATION RULES:

Set needs_tool = True IF:
- The input asks about system status, OS, CPU, RAM, IP, or local files.
- The input requests command execution or file operations.

Set needs_tool = False ONLY IF:
- General theory, concepts, or explanations (e.g., "What is a CPU?", "Explain what Python is").
- Writing code without executing it.
- Casual greeting or conversational chat without numbers/data.

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