import json
from typing import Any

from fastmcp import Client


class MCPClientManager:
    def __init__(self) -> None:
        self.client = Client("app/mcp/server.py")

    def _extract_text_from_result(self, result: Any) -> str:
        if hasattr(result, "content") and isinstance(result.content, list):
            texts: list[str] = []
            for item in result.content:
                if hasattr(item, "text"):
                    texts.append(str(item.text))
                elif isinstance(item, str):
                    texts.append(item)
            if texts:
                return "\n".join(texts).strip()

        if hasattr(result, "structuredContent") and result.structuredContent is not None:
            try:
                return json.dumps(result.structuredContent, ensure_ascii=False)
            except TypeError:
                return str(result.structuredContent)

        if isinstance(result, dict):
            safe_payload = {}
            for key in ("status", "message", "results", "matches_found", "data", "output"):
                if key in result:
                    safe_payload[key] = result[key]
            if safe_payload:
                return json.dumps(safe_payload, ensure_ascii=False)

        return str(result)

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

    async def execute_tool(self, tool_name: str, tool_args: dict | None = None) -> str:
        """Exec tool on mcp server and returns the cleaned result text."""
        async with self.client as session:
            result = await session.call_tool(tool_name, tool_args or {})
            return self._extract_text_from_result(result)[:2000]