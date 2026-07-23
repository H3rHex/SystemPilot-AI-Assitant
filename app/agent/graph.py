# app/agent/graph.py
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes.planner import planner_node
from app.agent.nodes.tool_getter import tool_getter_node
from app.agent.nodes.tool_runner import tool_runner_node
from app.agent.nodes.response_writer import response_writer_node

def route_planner(state: AgentState) -> str:
    if state.get("needs_tool", False):
        return "tool_getter"
    return "response_writer"

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("tool_getter", tool_getter_node)
workflow.add_node("tool_runner", tool_runner_node)
workflow.add_node("response_writer", response_writer_node)

# Set Entry Point
workflow.set_entry_point("planner")

# Add Edges
workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "tool_getter": "tool_getter",
        "response_writer": "response_writer"
    }
)

workflow.add_edge("tool_getter", "tool_runner")
workflow.add_edge("tool_runner", "response_writer")
workflow.add_edge("response_writer", END)

# Compile Graph
app_graph = workflow.compile()