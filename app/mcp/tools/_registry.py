from typing import Callable
from app.mcp.server_instance import mcp

import app.mcp.tools.system_info as system_tools
import app.mcp.tools.file_tools as file_tools


TOOL_MODULES = [
    system_tools.get_cpu_info,system_tools.get_network_info,system_tools.get_system_info,
    file_tools.create_file
]

def load_tools() -> None:
    """Ensures all tool modules are loaded into memory."""
    for tool in TOOL_MODULES:
        mcp.add_tool(tool)