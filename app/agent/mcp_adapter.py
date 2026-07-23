from typing import Any
from app.mcp.client import MCPClientManager

_mcp_client = MCPClientManager()

async def get_mcp_tools() -> list[dict[str, Any]]:
    """Retrieves tools from FastMCP client and simplifies their schema for the LLM."""
    formatted_tools = await _mcp_client.get_tools_for_llm()
    
    tools_catalog: list[dict[str, Any]] = []
    for item in formatted_tools:
        fn = item.get("function", {})
        tools_catalog.append({
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "inputSchema": fn.get("parameters", {})
        })
        
    return tools_catalog

async def execute_mcp_tool(tool_name: str, tool_args: dict[str, Any] | None = None) -> str:
    """Executes a tool on the FastMCP server asynchronously."""
    try:
        return await _mcp_client.execute_tool(tool_name, tool_args or {})
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"