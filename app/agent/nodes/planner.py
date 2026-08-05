import asyncio
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agent.config import LLM_TIMEOUT
from app.agent.llm import get_llm
from app.agent.observability import observe
from app.agent.state import AgentState


class PlannerOutput(BaseModel):
    reasoning: str = Field(
        description="Short explanation of why this request should be handled with or without tools."
    )
    goal: str = Field(
        description="Normalized end goal in one sentence, independent of the user phrasing."
    )
    needs_tool: bool = Field(
        description="Set to True only when the task requires current system state, files, runtime data, or a real action in the environment. Default to False for ordinary conversation."
    )
    tool_strategy: str = Field(
        description="One of: 'chat_only', 'system_probe', 'system_action', 'mixed'. Use 'chat_only' when a direct answer is enough; use 'system_probe' or 'system_action' when the environment must be inspected or changed."
    )
    context_summary: str = Field(
        description="Very short summary of what context is relevant to this request, without over-describing the environment."
    )


llm = get_llm(0.0)
structured_llm = llm.with_structured_output(PlannerOutput)


SYSTEM_PROMPT = """You are the planning layer for a general-purpose agent.

Your job is to interpret the user request and decide whether it can be answered directly or whether it requires current system or file context.

CORE RULES:
- Prefer direct chat answers for normal conversation, definitions, summarization, comparisons, greetings, or general knowledge.
- Set needs_tool = False for anything that can be answered from language alone, without reading files, querying the system, or acting on the environment.
- Set needs_tool = True only when the request depends on current files, directories, the OS, environment state, existing saved data, or a real action that must be executed.
- Keep the goal short, concrete, and user-oriented.
- Use tool_strategy to express the best execution mode:
  - 'chat_only': direct answer, no tools.
  - 'system_probe': read/inspect system state, files, or data sources.
  - 'system_action': do a real action or mutation on the environment.
  - 'mixed': a combination of inspection and action.

EXAMPLES:

User: "¿Qué es Python?"
Reasoning: General conceptual explanation; no live system info needed.
goal: Explain what Python is.
needs_tool: False
tool_strategy: chat_only
context_summary: General programming definition; no runtime context required.

User: "Lista el contenido de Downloads"
Reasoning: This needs the real filesystem state.
goal: Inspect the Downloads directory contents.
needs_tool: True
tool_strategy: system_probe
context_summary: Need to list the contents of the target directory.

"""


def _build_context_state(state: AgentState) -> str:
    context = state.get("context", {}) or {}
    facts = state.get("facts", []) or []
    if not context and not facts:
        return "No prior environment context available."

    summary_parts: list[str] = []
    if context:
        summary_parts.append(f"Context: {context}")
    if facts:
        recent_facts = facts[-3:]
        summary_parts.append(f"Known facts: {recent_facts}")
    return "\n".join(summary_parts)


@observe(name="planner_node", as_type="chain")
async def planner_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """Planner Node: Interpret the request and decide whether tools are necessary.

    The planner is responsible for intent analysis, final objective formation, and
    choosing the execution strategy. It is not just a boolean switch.
    """
    user_input = state["input"]
    context_state = _build_context_state(state)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"User request: {user_input}\n\n"
                f"Current agent state context:\n{context_state}"
            )
        ),
    ]

    configurable = config.get("configurable", {}) if config else {}
    timeout_seconds = configurable.get("planner_timeout", LLM_TIMEOUT)

    try:
        response = await asyncio.wait_for(
            structured_llm.ainvoke(messages),
            timeout=float(timeout_seconds),
        )
        response = cast(PlannerOutput, response)

        phase = "inspect" if response.needs_tool else "finalize"

        return {
            "phase": phase,
            "goal": response.goal,
            "needs_tool": response.needs_tool,
            "context": {
                "tool_strategy": response.tool_strategy,
                "context_summary": response.context_summary,
                "planner_reasoning": response.reasoning,
            },
            "facts": [
                {
                    "key": "planner_goal",
                    "value": response.goal,
                    "type": "string",
                    "source": "planner",
                    "metadata": {"needs_tool": response.needs_tool},
                },
                {
                    "key": "planner_decision",
                    "value": response.tool_strategy,
                    "type": "string",
                    "source": "planner",
                    "metadata": {"reasoning": response.reasoning},
                },
            ],
            "error": None,
        }

    except asyncio.TimeoutError:
        return {
            "phase": "error",
            "goal": "Resolve the user request safely.",
            "needs_tool": False,
            "context": {
                "tool_strategy": "chat_only",
                "context_summary": "The planner timed out; fallback to a safe direct response.",
                "planner_reasoning": f"Planner node timed out after {timeout_seconds} seconds.",
            },
            "facts": [],
            "error": "PLANNER_TIMEOUT",
        }

    except Exception as e:
        return {
            "phase": "error",
            "goal": "Resolve the user request safely.",
            "needs_tool": False,
            "context": {
                "tool_strategy": "chat_only",
                "context_summary": "The planner failed; fallback to a safe direct response.",
                "planner_reasoning": f"Planner execution failed: {str(e)}",
            },
            "facts": [],
            "error": "PLANNER_ERROR",
        }