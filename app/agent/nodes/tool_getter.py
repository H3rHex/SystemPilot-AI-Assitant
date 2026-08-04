# app/agent/nodes/tool_getter.py
import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools

llm = get_llm(temperature=0.0)

SYSTEM_PROMPT = """You are the Tool Selection Module for SystemPilot.

Your job is to select the appropriate tool and populate its arguments matching its schema.

GENERAL DIRECTIVES:
1. ARGUMENT COMPLETENESS: Generate all required content/text inside tool arguments.
2. PATH RESOLUTION: When operating on items from a previous listing tool, construct the full absolute path by joining `target_directory` + `/` + `item.name` (e.g., `/home/user/Downloads/file.txt`). NEVER pass a directory path to a file-level tool like `delete_file`.
3. CONDITIONAL COMPLETION: If a previous tool output returned empty results (`items: []` or `total_items: 0`) and the task is conditional ("if present then delete"), DO NOT CALL ANY MORE TOOLS. Your work is done.
4. NO REPETITION OR RETRIES ON ERROR: Do NOT call the same tool with the exact same arguments if it has already been executed successfully.
5. SEQUENTIAL EXECUTION: Return AT MOST ONE tool call per step.
6. DO NOT BLACKLIST ALL TOOLS IN A STEP: if a prior tool result is similar, keep the best valid action instead of returning zero tools.
"""


def format_history_for_getter(tool_results: list[dict[str, Any]]) -> str:
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
    user_input = state["input"]
    tool_results = state.get("tool_results", [])

    all_tools = await get_mcp_tools()
    available_tools = all_tools

    llm_with_tools = llm.bind_tools(available_tools)

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    if tool_results:
        history_text = format_history_for_getter(tool_results)
        messages.append(HumanMessage(
            content=f"Original Request: {user_input}\n\nExecuted Tools History:\n{history_text}"
        ))
    else:
        messages.append(HumanMessage(content=f"User Request: {user_input}"))

    response = await llm_with_tools.ainvoke(messages)
    tool_calls = response.tool_calls or []

    executed_signatures = {
        _tool_signature(item.get("tool", ""), item.get("args", {}))
        for item in tool_results
        if item.get("result") is not None and "error" not in item
    }

    valid_tool_calls = []
    for tc in tool_calls:
        call_signature = _tool_signature(tc.get("name", ""), tc.get("args", {}))
        if call_signature not in executed_signatures:
            valid_tool_calls.append(tc)

    if not valid_tool_calls and tool_calls:
        valid_tool_calls = [tool_calls[0]]

    if len(valid_tool_calls) > 1:
        valid_tool_calls = valid_tool_calls[:1]

    selected_tools_payload = [
        {"name": tc["name"], "args": tc["args"]}
        for tc in valid_tool_calls
    ]

    return {"selected_tools": selected_tools_payload}