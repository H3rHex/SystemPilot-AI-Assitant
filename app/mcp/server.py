import sys
import os

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["FASTMCP_LOG_ENABLED"] = "false"

from fastmcp import FastMCP
from app.mcp.tools.system_info import get_system_info



mcp = FastMCP("SystemPilot MCP Server")
tools = [get_system_info]

for tool in tools:
    mcp.tool()(tool)

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)