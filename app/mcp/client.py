from fastmcp import Client

class MCPClientManager:
    def __init__(self) -> None:
        self.client = Client("app/mcp/server.py")
    
    async def get_tools_for_llm(self) -> list[dict]:
        """Returns mcp server tools"""
        async with self.client as session:
            mcp_tools = await session.list_tools()
            return [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema
                    }
                }
                for tool in mcp_tools
            ]
    
    async def execute_tool(self, tool_name: str, tool_args:dict | None = None) -> str:
        """Exec tool on mcp server and returns server reponse"""
        async with self.client as session:
            result = await session.call_tool(tool_name, tool_args or {})
            return str(result)