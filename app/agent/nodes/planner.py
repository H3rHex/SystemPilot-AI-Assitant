import os
from typing import cast
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm


# 1. CAMBIO CRÍTICO: 'reasoning' va PRIMERO para forzar Chain-of-Thought (CoT)
class PlannerOutput(BaseModel):
    reasoning: str = Field(
        description="One short sentence explaining why a tool is or isn't required based on whether the user asks for external state, file/directory inspection, or execution vs pure text."
    )
    needs_tool: bool = Field(
        description="True if external execution, tool invocation, or system state/file inspection is needed. False STRICTLY for pure theoretical answers or greetings."
    )


llm = get_llm(0.0)
structured_llm = llm.with_structured_output(PlannerOutput)

SYSTEM_PROMPT = """Analyze the user request to determine if it requires interacting with the system, external tools, or environment, or if it can be answered using purely internal static knowledge.

CLASSIFICATION PRINCIPLES:

Set needs_tool = True IF:
- The request asks to list, view, inspect, search, create, modify, or delete files or directories (e.g., "Lista la carpeta...", "Muestra el directorio", "Lee el archivo...").
- The request includes explicit file system paths (e.g., '/home/...', 'C:\\...', './...').
- The request asks about system status, capabilities, or available tools.
- The request requires fetching, executing, or verifying ANY external, dynamic, or real-time state.

Set needs_tool = False STRICTLY ONLY IF:
- Pure conceptual explanations, theories, or general knowledge (e.g., "What is Linux?", "Explain Python").
- Generating text or code snippets without any request to inspect, run, or save them to disk.
- Casual greetings or general conversational chat with no action requested.

DEFAULT RULE:
When in doubt, or if any action verb/system path is mentioned -> ALWAYS set needs_tool = True.
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
        "needs_tool": response.needs_tool,
        "planner_reasoning": response.reasoning
    }