# app/mcp/server.py
import sys
from pathlib import Path

# Insertamos la raíz del proyecto (SystemPilot) en el sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastmcp import FastMCP
from app.mcp.tools.system_info import get_system_info

mcp = FastMCP("SystemPilot MCP Server")
tools = [get_system_info]

for tool in tools:
    mcp.tool()(tool)

if __name__ == "__main__":
    mcp.run(transport="stdio")