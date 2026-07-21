from typing import Literal
from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.config import MAX_TOOLS_PER_STEP, MAX_DRAFT_PER_STEP

from app.agent.nodes.planner import planner_node
from app.agent.nodes.tool_getter import tool_getter_node
from app.agent.nodes.tool_reviewer import tool_reviewer_node
from app.agent.nodes.drafter import drafter_node
from app.agent.nodes.reviewer import reviewer_node

from app.agent.edges import (
    route_planner,
    route_tool_reviewer,
    route_final_reviewer,
)

def create_agent_graph():
    builder = StateGraph(AgentState)

    # 1. Registrar Nodos
    builder.add_node("planner", planner_node)
    builder.add_node("tool_getter", tool_getter_node)
    builder.add_node("tool_reviewer", tool_reviewer_node)
    builder.add_node("drafter", drafter_node)
    builder.add_node("reviewer", reviewer_node)

    # 2. Conectar Flujo
    builder.add_edge(START, "planner")
    
    # Transiciones condicionales
    builder.add_conditional_edges("planner", route_planner)
    
    builder.add_edge("tool_getter", "tool_reviewer")
    builder.add_conditional_edges("tool_reviewer", route_tool_reviewer)
    
    builder.add_edge("drafter", "reviewer")
    builder.add_conditional_edges("reviewer", route_final_reviewer)

    return builder.compile()

# Instancia ejecutable del grafo
agent_graph = create_agent_graph()