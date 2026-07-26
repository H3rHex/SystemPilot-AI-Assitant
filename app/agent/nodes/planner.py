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

SYSTEM_PROMPT = """Analyze if the user request requires executing a tool, inspecting local system state, or performing file operations.

MANDATORY DIRECTIVES:
1. ACTION OVER CONTENT RULE (CRITICAL): If the user request contains action verbs related to files (e.g., "create", "write", "generate", "save", "make", "delete", "crea", "escribe", "guarda") targeting disk/files, it MUST be classified as needs_tool = True, REGARDLESS of the topic or content requested.
2. LOCAL SYSTEM POLICY: Any query asking about "my system", "my OS", "my computer", "my PC", hardware, processes, or local files refers to LOCAL DATA and MUST use a tool.
3. COMMAND EXECUTION: Any request to run commands, scripts, or modify system files MUST use a tool.

CLASSIFICATION RULES:

Set needs_tool = True IF:
- The user requests ANY file creation or modification, even if it involves generating text/code on a topic (e.g., "crea un archivo sobre Python", "write a note about history", "save a script").
- The user asks about system status, OS, CPU, RAM, IP, processes, or local file lists.
- The user requests running shell/terminal commands.

Set needs_tool = False STRICTLY ONLY IF:
- Pure conceptual queries WITH NO FILE OR SYSTEM ACTION REQUESTED (e.g., "What is Linux?", "Explain Python", "How does TCP work?").
- Writing code snippets in chat WITHOUT any request to write, create, or save a file.
- Casual greetings or general conversational chat.

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