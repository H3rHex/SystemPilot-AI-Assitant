# app/agent/nodes/tool_runner.py
from typing import Any

from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.mcp_adapter import execute_mcp_tool


def clean_mcp_result(result: Any) -> str:
    if isinstance(result, str):
        return result.strip()[:2000]

    if isinstance(result, dict):
        payload = {}
        for key in ("status", "message", "results", "matches_found", "data", "output"):
            if key in result:
                payload[key] = result[key]
        if payload:
            return str(payload)[:2000]

    text = str(result)
    if "content" in text and "annotations" in text:
        return text.split("content=")[-1].split(", annotations=")[0][:2000]
    return text[:2000]


@observe(name="tool_runner_node", as_type="tool")
async def tool_runner_node(state: AgentState) -> dict:
    selected_tools = state.get("selected_tools", [])
    current_history = state.get("tool_results", [])

    new_results = []

    for tool in selected_tools:
        name = str(tool.get("name"))
        args = tool.get("args", {})

        try:
            raw_result = await execute_mcp_tool(name, args)
            clean_res = clean_mcp_result(raw_result)
            new_results.append({
                "tool": name,
                "args": args,
                "result": clean_res
            })
        except Exception as e:
            new_results.append({"tool": name, "args": args, "error": str(e)[:2000]})

    return {
        "tool_results": (current_history + new_results)[-5:],
        "selected_tools": []
    }