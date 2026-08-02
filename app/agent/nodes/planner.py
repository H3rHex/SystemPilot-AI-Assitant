import os
import asyncio
from typing import cast
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.config import LLM_TIMEOUT


class PlannerOutput(BaseModel):
    reasoning: str = Field(
        description="Short reason for the decision."
    )
    needs_tool: bool = Field(
        description="DEFAULT IS TRUE. Set to False STRICTLY ONLY for static definitions, trivia, or general text generation."
    )


llm = get_llm(0.0)
structured_llm = llm.with_structured_output(PlannerOutput)


SYSTEM_PROMPT = """You are a deterministic tool requirement classifier.

DEFAULT RULE:
Set needs_tool = True by default.

MANDATORY TOOL TRIGGERS (needs_tool = True):
- Help or capabilities requests (e.g., "help", "ayuda", "what can you do?").
- File, path, or directory operations (e.g., "notes.txt", "Downloads", "/home/user").
- Any action verb on disk or system state (e.g., list, read, search, create, delete).

EXEMPTION RULES (needs_tool = False STRICTLY ONLY IF):
- Pure conceptual definitions or general trivia (e.g., "What is Python?", "Is a 40kg dog heavy?").
- Casual greetings or pleasantries (e.g., "Hello", "How are you?").
- Pure in-memory text/code generation without saving or execution requests.

FEW-SHOT EXAMPLES:

User: "ayuda"
Reasoning: System capability request requiring tool invocation.
needs_tool: True

User: "What is Python?"
Reasoning: Pure conceptual definition query.
needs_tool: False

User: "Is a 40kg dog heavy?"
Reasoning: General knowledge trivia request.
needs_tool: False

User: "List files in Downloads"
Reasoning: Local directory inspection request.
needs_tool: True
"""


@observe(name="planner_node", as_type="chain")
async def planner_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """Planner Node: Evaluates user input and decides whether tools are required.
    
    Includes an explicit timeout and error state handling.
    """
    user_input = state["input"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    configurable = config.get("configurable", {}) if config else {}
    timeout_seconds = configurable.get("planner_timeout", LLM_TIMEOUT)

    try:
        response = await asyncio.wait_for(
            structured_llm.ainvoke(messages),
            timeout=float(timeout_seconds)
        )
        response = cast(PlannerOutput, response)

        return {
            "needs_tool": response.needs_tool,
            "planner_reasoning": response.reasoning,
            "error": None
        }

    except asyncio.TimeoutError:
        return {
            "needs_tool": False,
            "planner_reasoning": f"Planner node timed out after {timeout_seconds} seconds.",
            "error": "PLANNER_TIMEOUT"
        }

    except Exception as e:
        return {
            "needs_tool": False,
            "planner_reasoning": f"Planner execution failed: {str(e)}",
            "error": "PLANNER_ERROR"
        }