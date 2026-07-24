import sys
import os

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["FASTMCP_LOG_ENABLED"] = "false"

import app.mcp.tools
from app.mcp.server_instance import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)