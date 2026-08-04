from typing import TypedDict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    input: str
    needs_tool: bool
    needs_another_tool:bool
    next_tool_step_count: int
    selected_tools: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    final_response: str
    error: str | None