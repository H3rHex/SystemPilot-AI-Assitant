import asyncio
from typing import Any
from app.mcp.client import MCPClientManager

class MCPAdapter:
    """Synchronous adapter bridging AgentEngine with the async MCPClientManager."""
    
    def __init__(self) -> None:
        self.client = MCPClientManager()

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch tools available on the MCP server."""
        try:
            return asyncio.run(self.client.get_tools_for_llm())
        except Exception:
            return []

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool synchronously on the MCP server."""
        try:
            return asyncio.run(self.client.execute_tool(name, arguments))
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"