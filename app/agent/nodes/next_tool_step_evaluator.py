# app/agent/nodes/next_tool_step_evaluator.py
import asyncio
from typing import Any, cast

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm


class StepEvaluatorOutput(BaseModel):
    reasoning: str = Field(
        description=(
            "Step-by-step evaluation comparing the user's intent against completed tool results. "
            "Explicitly list: 1) Completed actions, 2) Pending or unfulfilled actions."
        )
    )
    needs_another_tool: bool = Field(
        description=(
            "MUST be True if ANY requested action, conditional step, or follow-up operation "
            "remains unexecuted. MUST be False ONLY when ALL user goals are completely satisfied."
        )
    )

llm = get_llm(0.0)
structured_llm = llm.with_structured_output(StepEvaluatorOutput)

SYSTEM_PROMPT = """You are the Task Completion Evaluator for SystemPilot.

Your sole responsibility is to compare the Original User Request against the Executed Tools History to determine if additional tool calls are required.

EVALUATION PROTOCOL:
1. DISSECT INTENT: Identify all primary, secondary, and conditional actions requested by the user (e.g., "Do X, and if Y then do Z").
2. AUDIT HISTORY: Match each requested action against the tools already executed in the history.
3. IDENTIFY GAPS: Determine if any requested action, sub-task, or conditional trigger remains unfulfilled.

STRICT DECISION RULES:
- If ANY part of the user's request (including conditional or follow-up steps) has NOT been executed, set `needs_another_tool = True`.
- Set `needs_another_tool = False` ONLY AND EXCLUSIVELY if every single action requested by the user is fully satisfied by the executed tools history.

CRITICAL CONSISTENCY MANDATE:
- Your `needs_another_tool` boolean value MUST strictly align with your `reasoning`. 
- If your reasoning mentions a pending action, unfulfilled request, or next step, setting `needs_another_tool = False` IS A CRITICAL ERROR.
"""


def format_tool_results(tool_results: list[dict[str, Any]]) -> str:
    if not tool_results:
        return "No tools executed yet."

    recent = tool_results[-3:]
    summary = []
    for i, item in enumerate(recent, 1):
        tool_name = item.get("tool", "unknown_tool")
        args = item.get("args", {})
        result = item.get("result", item.get("error", ""))
        result_text = str(result).strip()
        if len(result_text) > 900:
            result_text = result_text[:900] + "..."
        summary.append(f"{i}. {tool_name}({args}) -> Result:\n{result_text}")

    return "\n---\n".join(summary)


@observe(name="next_tool_step_evaluator", as_type="chain")
async def next_tool_step_evaluator(state: AgentState, config: RunnableConfig | None = None) -> dict:
    user_input = state["input"]
    tool_results = state.get("tool_results", [])
    current_step_count = state.get("next_tool_step_count", 0) + 1

    formatted_history = format_tool_results(tool_results)

    evaluation_context = (
        f"Original User Request: {user_input}\n\n"
        f"Executed Tools History:\n{formatted_history}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=evaluation_context)
    ]

    try:
        response = await structured_llm.ainvoke(messages)
        if isinstance(response, dict):
            response = StepEvaluatorOutput(**response)

        return {
            "needs_another_tool": response.needs_another_tool,
            "step_evaluator_reasoning": response.reasoning,
            "next_tool_step_count": current_step_count,
            "error": None
        }

    except Exception as e:
        return {
            "needs_another_tool": False,
            "step_evaluator_reasoning": f"Step evaluator execution failed: {str(e)}",
            "next_tool_step_count": current_step_count,
            "error": "STEP_EVALUATOR_ERROR"
        }