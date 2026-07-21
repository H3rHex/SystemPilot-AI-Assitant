# app/agent/edges.py
from typing import Literal
from langgraph.graph import END
from app.agent.state import AgentState
from app.agent.config import MAX_DRAFT_PER_STEP, MAX_TOOLS_PER_STEP

def route_planner(state: AgentState) -> Literal["tool_getter", "drafter"]:
    if state.get("needs_tool", False):
        return "tool_getter"
    return "drafter"

def route_tool_reviewer(state: AgentState) -> Literal["drafter", "tool_getter"]:
    is_approved = state.get("is_approved", False)
    retry_count = state.get("retry_count", 0)

    if is_approved or retry_count >= MAX_TOOLS_PER_STEP:
        return "drafter"
    return "tool_getter"

def route_final_reviewer(state: AgentState) -> Literal["__end__", "drafter"]:
    is_approved = state.get("is_final_approved", False)
    retry_count = state.get("response_retry_count", 0)

    if is_approved or retry_count >= MAX_DRAFT_PER_STEP:
        return "__end__"
    return "drafter"