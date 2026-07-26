# app/agent/nodes/tool_getter.py
from typing import cast
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools

llm = get_llm(temperature=0.0)

SYSTEM_PROMPT = """You are the Tool Selection Module for SystemPilot.
Select the necessary tool(s) to fulfill the user request based on the provided tool definitions.
If no tool is required, do not invoke any tool."""

@observe(name="tool_getter_node", as_type="chain")
async def tool_getter_node(state: AgentState) -> dict:
    user_input = state["input"]
    discarded = state.get("discarded_tools", [])
    
    all_tools = await get_mcp_tools() 
    available_tools = [t for t in all_tools if t["name"] not in discarded]    
    llm_with_tools = llm.bind_tools(available_tools)
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User Request: {user_input}")
    ]
    
    response = await llm_with_tools.ainvoke(messages)
    
    selected_tools_payload = []
    if response.tool_calls:
        for tc in response.tool_calls:
            selected_tools_payload.append({
                "name": tc["name"],
                "args": tc["args"]
            })

    return {
        "selected_tools": selected_tools_payload
    }