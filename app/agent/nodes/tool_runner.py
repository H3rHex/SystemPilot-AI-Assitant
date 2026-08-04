# app/agent/nodes/tool_runner.py
from typing import Any
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.mcp_adapter import execute_mcp_tool

def clean_mcp_result(result: Any) -> str:
    if hasattr(result, "content") and isinstance(result.content, list):
        extracted = [item.text for item in result.content if hasattr(item, "text")]
        if extracted:
            return "\n".join(extracted)
    elif isinstance(result, dict) and "content" in result:
        return str(result["content"])
    return str(result)

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
            new_results.append({"tool": name, "args": args, "error": str(e)})

    return {
        "tool_results": current_history + new_results,
        "selected_tools": []  
    }