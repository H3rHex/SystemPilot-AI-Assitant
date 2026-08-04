# app/agent/graph.py
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes.planner import planner_node
from app.agent.nodes.tool_getter import tool_getter_node
from app.agent.nodes.tool_runner import tool_runner_node
from app.agent.nodes.response_writer import response_writer_node
from app.agent.nodes.fallback_node import fallback_node
from app.agent.nodes.next_tool_step_evaluator import next_tool_step_evaluator


def route_planner(state: AgentState) -> str:
    if state.get("error"):
        return "fallback_node"

    if state.get("needs_tool", False):
        return "tool_getter"

    return "response_writer"

def route_next_tool_step_evaluator(state: AgentState) -> str:
    if state.get("error"):
        return "fallback_node"

    if state.get("needs_another_tool", False):
        return "tool_getter"

    return "response_writer"

workflow = StateGraph(AgentState)

# ADD NODES
workflow.add_node("planner", planner_node)
workflow.add_node("next_tool_step_evaluator", next_tool_step_evaluator)
workflow.add_node("tool_getter", tool_getter_node)
workflow.add_node("tool_runner", tool_runner_node)
workflow.add_node("response_writer", response_writer_node)
workflow.add_node("fallback_node", fallback_node)

# --- ADD EDGES ---

# PLANNER NODE
workflow.set_entry_point("planner")

workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "tool_getter": "tool_getter",
        "response_writer": "response_writer",
        "fallback_node": "fallback_node"
    }
)

# TOOLS NODES
workflow.add_edge("tool_getter", "tool_runner")
workflow.add_edge("tool_runner", "next_tool_step_evaluator")
workflow.add_conditional_edges(
    "next_tool_step_evaluator",
    route_next_tool_step_evaluator,
    {
        "tool_getter": "tool_getter",
        "response_writer": "response_writer",
        "fallback_node": "fallback_node"
    }
)

# RESPONSE NODES
workflow.add_edge("response_writer", END)
workflow.add_edge("fallback_node", END)

app_graph = workflow.compile()