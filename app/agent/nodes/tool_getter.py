import json
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools
from app.agent.observability import observe
from app.agent.state import AgentState, FactEntry, ToolResultEntry

llm = get_llm(temperature=0.0)

SYSTEM_PROMPT = """You are a bounded action selector.

Your responsibility is to choose exactly ONE next tool call for the current phase based on user intent and current state.
Do not orchestrate the whole workflow. Do not try to predict future steps. Do not invent missing data.

Hard rules:
1. Only choose a tool that is logically valid for the current phase, goal, and context.
2. Rely on Known Facts, Working Memory, and Planner Context to decide the next concrete tool call.
3. Return at most one tool call matching the exact schema parameters of the tool.
4. If no valid action exists or the objective is already achieved, return no tool call.
5. Never repeat a call with the same arguments if it already succeeded.
"""


def _format_facts(facts: list[FactEntry]) -> str:
    if not facts:
        return "None"
    formatted = []
    for f in facts[-5:]:
        key = f.get("key", "unknown")
        val = f.get("value")
        formatted.append(f"- {key}: {val}")
    return "\n".join(formatted)


def _format_last_tool(tool_name: str | None, tool_args: dict[str, Any]) -> str:
    if not tool_name:
        return "None"
    return f"{tool_name}(args={json.dumps(tool_args)})"


def _format_dict_block(data: dict[str, Any]) -> str:
    if not data:
        return "None"
    return json.dumps(data, indent=2, default=str)


def format_history_for_getter(tool_results: Sequence[ToolResultEntry]) -> str:
    if not tool_results:
        return "None"
    formatted = []
    for item in tool_results[-3:]:
        tool = item.get("tool")
        args = item.get("args")
        result = item.get("result") or item.get("error") or ""
        formatted.append(f"Executed: {tool}(args={args})\nOutput:\n{result}\n")
    return "\n---\n".join(formatted)


def _tool_signature(tool_name: str, tool_args: dict[str, Any] | None) -> str:
    payload = tool_args or {}
    return json.dumps({"name": tool_name, "args": payload}, sort_keys=True, default=str)


@observe(name="tool_getter_node", as_type="chain")
async def tool_getter_node(state: AgentState) -> dict:
    phase = state.get("phase", "plan")
    goal = state.get("goal") or state.get("input", "")
    context = state.get("context", {})
    facts = state.get("facts", [])
    working_memory = state.get("working_memory", {})
    last_tool_name = state.get("last_tool_name")
    last_tool_args = state.get("last_tool_args", {})
    tool_results = state.get("tool_results", [])

    available_tools = await get_mcp_tools()
    if not available_tools:
        return {"selected_tools": []}

    llm_with_tools = llm.bind_tools(available_tools)

    prompt_content = (
        f"Goal: {goal}\n"
        f"Current Phase: {phase}\n\n"
        f"Context ===\n{_format_dict_block(context)}\n\n"
        f"Known Facts ===\n{_format_facts(facts)}\n\n"
        f"Working Memory ===\n{_format_dict_block(working_memory)}\n\n"
        f"Last Executed Tool ===\n{_format_last_tool(last_tool_name, last_tool_args)}\n\n"
        f"Tool Execution History ===\n{format_history_for_getter(tool_results)}"
    )

    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt_content),
    ]

    response = await llm_with_tools.ainvoke(messages)
    tool_calls = response.tool_calls or []

    executed_signatures = {
        _tool_signature(item.get("tool", ""), item.get("args", {}))
        for item in tool_results
        if item.get("result") is not None and "error" not in item
    }

    valid_tool_calls = []
    for tc in tool_calls[:1]:
        tool_name = str(tc.get("name", ""))
        allowed_names = {str(tool.get("name", "")) for tool in available_tools}
        if tool_name not in allowed_names:
            continue

        args = dict(tc.get("args", {}))
        signature = _tool_signature(tool_name, args)

        if signature not in executed_signatures:
            valid_tool_calls.append({"name": tool_name, "args": args})

    return {"selected_tools": valid_tool_calls}