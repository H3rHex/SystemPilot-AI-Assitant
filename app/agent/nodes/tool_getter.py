import json

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools
from app.agent.observability import observe
from app.agent.state import AgentState, ToolResultEntry

llm = get_llm(temperature=0.0)

READ_LIKE_KEYWORDS = (
    "list", "find", "search", "read", "get", "inspect", "lookup",
    "describe", "query", "fetch", "show", "dir", "ls", "stat", "info",
    "open"
)
WRITE_LIKE_KEYWORDS = (
    "create", "write", "save", "update", "delete", "remove", "rename",
    "move", "copy", "modify", "execute", "run", "apply", "set", "put",
    "post", "patch"
)


def _tool_role(name: str) -> str:
    lowered = name.lower()
    if any(keyword in lowered for keyword in WRITE_LIKE_KEYWORDS):
        return "write"
    if any(keyword in lowered for keyword in READ_LIKE_KEYWORDS):
        return "read"
    return "other"


def _filter_tools_for_phase(phase: str, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phase_roles: dict[str, set[str]] = {
        "idle": {"read", "write"},
        "plan": {"read"},
        "inspect": {"read"},
        "evaluate_results": {"read", "write"},
        "finalize": {"read", "write"},
        "done": set(),
        "error": set(),
    }

    allowed_roles = phase_roles.get(phase, {"read", "write"})
    return [
        tool for tool in tools
        if _tool_role(str(tool.get("name", ""))) in allowed_roles
    ]


SYSTEM_PROMPT = """You are a bounded action selector.

Your responsibility is to choose exactly ONE next tool call for the current phase.
Do not orchestrate the whole workflow. Do not try to predict future steps. Do not invent missing data.

Hard rules:
1. Only choose a tool that is valid for the current phase.
2. Use goal, phase, and pending_targets as the reasoning frame; do not assume a fixed workflow.
3. Prefer actions that target explicit pending_targets when they exist.
4. Return at most one tool call.
5. If no valid action exists, return no tool call.
6. Never pass a list where the tool schema expects a string. Collapse list-like path arguments to the first valid item.
7. Never repeat a call with the same arguments if it already succeeded.
8. This selector is intentionally narrow: it picks the next valid action, not the whole execution plan.
"""


def format_history_for_getter(tool_results: Sequence[ToolResultEntry]) -> str:
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


def _normalize_pending_targets(raw_targets: Any) -> list[str]:
    if raw_targets is None:
        return []
    if isinstance(raw_targets, str):
        return [raw_targets]
    if isinstance(raw_targets, dict):
        candidates = [
            raw_targets.get("value"),
            raw_targets.get("path"),
            raw_targets.get("target"),
            raw_targets.get("name"),
            raw_targets.get("uri"),
            raw_targets.get("location"),
        ]
        return [str(item) for item in candidates if item not in (None, "")]
    if isinstance(raw_targets, list):
        flattened: list[str] = []
        for item in raw_targets:
            flattened.extend(_normalize_pending_targets(item))
        return flattened
    return [str(raw_targets)]


def _sanitize_tool_args(args: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(args or {})
    for key in [
        "path", "target", "uri", "location", "directory",
        "search_directory", "filename", "file_path", "file_name",
        "input", "query", "name"
    ]:
        value = sanitized.get(key)
        if isinstance(value, list) and value:
            sanitized[key] = value[0]
        elif isinstance(value, tuple) and value:
            sanitized[key] = value[0]
    return sanitized


@observe(name="tool_getter_node", as_type="chain")
async def tool_getter_node(state: AgentState) -> dict:
    user_input = state["input"]
    tool_results = state.get("tool_results", [])
    phase = state.get("phase", "plan")
    goal = state.get("goal") or user_input
    working_memory = state.get("working_memory", {}) or {}
    pending_targets = _normalize_pending_targets(working_memory.get("pending_targets", []))

    all_tools = await get_mcp_tools()
    available_tools = _filter_tools_for_phase(phase, all_tools)

    if not available_tools:
        return {"selected_tools": []}

    llm_with_tools = llm.bind_tools(available_tools)

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    if tool_results:
        history_text = format_history_for_getter(tool_results)
        messages.append(
            HumanMessage(
                content=(
                    f"Original Request: {user_input}\n"
                    f"Goal: {goal}\n"
                    f"Current Phase: {phase}\n"
                    f"Pending Targets: {pending_targets}\n\n"
                    f"Executed Tools History:\n{history_text}"
                )
            )
        )
    else:
        messages.append(
            HumanMessage(
                content=(
                    f"User Request: {user_input}\n"
                    f"Goal: {goal}\n"
                    f"Current Phase: {phase}\n"
                    f"Pending Targets: {pending_targets}"
                )
            )
        )

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
        args = _sanitize_tool_args(tc.get("args", {}))
        signature = _tool_signature(tool_name, args)
        if signature not in executed_signatures:
            valid_tool_calls.append({"name": tool_name, "args": args})

    if pending_targets and valid_tool_calls:
        primary_target = pending_targets[0]
        preferred_key = "path"
        for key in ("path", "target", "uri", "location", "directory", "search_directory", "filename", "file_path", "file_name", "input", "query", "name"):
            if key in valid_tool_calls[0]["args"]:
                preferred_key = key
                break
        valid_tool_calls[0]["args"].setdefault(preferred_key, primary_target)

    return {"selected_tools": valid_tool_calls}