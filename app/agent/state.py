# app/agent/state.py
from typing import TypedDict, Any

class AgentState(TypedDict):
    input: str
    needs_tool: bool
    selected_tools: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    final_response: str
    error: str | None