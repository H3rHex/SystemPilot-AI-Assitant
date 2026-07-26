from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.mcp_adapter import execute_mcp_tool

@observe(name="tool_runner_node", as_type="tool")
async def tool_runner_node(state: AgentState) -> dict:
    selected_tools = state.get("selected_tools", [])
    current_history = state.get("tool_results", [])
    
    new_results = []

    for tool in selected_tools:
        name = str(tool.get("name"))
        args = tool.get("args", {})
        
        try:
            result = await execute_mcp_tool(name, args)
            new_results.append({"tool": name, "result": result})
        except Exception as e:
            new_results.append({"tool": name, "error": str(e)})

    updated_tool_results = current_history + new_results

    return {
        "tool_results": updated_tool_results,
        "selected_tools": []  
    }