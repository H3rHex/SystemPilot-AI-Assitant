import json
from pydantic import Field
from app.mcp.server_instance import mcp
from app.agent.mcp_adapter import get_mcp_tools


@mcp.tool()
async def get_system_capabilities() -> str:
    """Retrieve a complete, real-time list of all currently registered system tools, including their descriptions and input parameters.

    LLM INSTRUCTIONS:
    - ALWAYS invoke this tool when the user asks about your capabilities, functions, available tools, or requests help/documentation.
    - DO NOT invent or assume tools from memory. Use the output of this function as the single source of truth to answer what you can do.

    USE THIS TOOL WHEN THE USER ASKS:
    - '¿Qué puedes hacer?' / 'What can you do?'
    - '¿Qué herramientas tienes disponibles?' / 'What tools do you have?'
    - 'Muestra tus funciones, comandos o capacidades'
    - 'Ayuda' / 'Help'
    """

    try:
        raw_tools = await get_mcp_tools()

        capabilities = []
        for tool in raw_tools:
            args_schema = tool.get("args_schema", {})
            properties = {}
            
            if hasattr(args_schema, "schema"):
                properties = args_schema.schema().get("properties", {})
            elif isinstance(args_schema, dict):
                properties = args_schema.get("properties", {})

            param_names = list(properties.keys())

            capabilities.append({
                "name": tool["name"],
                "description": tool["description"],
                "accepted_parameters": param_names
            })

        return json.dumps({
            "status": "success",
            "total_tools": len(capabilities),
            "tools": capabilities
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to retrieve capabilities: {str(e)}"
        }, indent=2)