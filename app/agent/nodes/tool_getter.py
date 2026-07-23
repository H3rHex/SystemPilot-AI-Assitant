# app/agent/nodes/tool_getter.py
from typing import Any, cast
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools

class ToolCall(BaseModel):
    tool_name: str = Field(description="The exact name of the selected tool.")
    tool_args: dict[str, Any] = Field(default_factory=dict, description="Arguments matching the tool schema.")

class ToolSelectionOutput(BaseModel):
    tools: list[ToolCall] = Field(default_factory=list)
    reasoning: str = Field(description="Why these specific tools were chosen.")

llm = get_llm(temperature=0.0)
structured_llm = llm.with_structured_output(ToolSelectionOutput)

SYSTEM_PROMPT = """You are the Tool Selection Module for SystemPilot.

Select necessary tools to fulfill the user request.

STRICT ARGUMENT RULES:
1. ONLY pass arguments that are explicitly defined in the tool's inputSchema.
2. DO NOT invent extra parameters or flags.
3. If a tool requires NO arguments, pass an empty object {{}}.

AVAILABLE TOOLS:
{tools_schema}

DISCARDED TOOLS:
{discarded_tools}
"""

def sanitize_args(proposed_args: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Filters out any arguments not defined in the tool's inputSchema."""
    if not schema or "properties" not in schema:
        return {}
    
    allowed_keys = set(schema["properties"].keys())
    sanitized = {k: v for k, v in proposed_args.items() if k in allowed_keys}
    
    removed_keys = set(proposed_args.keys()) - allowed_keys
    # if removed_keys:
    #     print(f"⚠️ [SANITIZER] Removed disallowed arguments: {removed_keys}")
        
    return sanitized

async def tool_getter_node(state: AgentState) -> dict:
    user_input = state["input"]
    discarded = state.get("discarded_tools", [])
    
    all_tools = await get_mcp_tools()
    available_tools = [t for t in all_tools if t["name"] not in discarded]
    
    tool_schemas = {t["name"]: t.get("inputSchema", {}) for t in available_tools}
    
    tools_str = "\n".join(
        [f"- Name: {t['name']}\n  Description: {t['description']}\n  Schema: {t.get('inputSchema', {})}" for t in available_tools]
    )
    discarded_str = ", ".join(discarded) if discarded else "None"
    
    formatted_system_prompt = SYSTEM_PROMPT.format(
        tools_schema=tools_str if tools_str else "NO TOOLS AVAILABLE",
        discarded_tools=discarded_str
    )
    
    messages = [
        SystemMessage(content=formatted_system_prompt),
        HumanMessage(content=f"User Request: {user_input}")
    ]
    
    response = cast(ToolSelectionOutput, await structured_llm.ainvoke(messages))
    
    selected_tools_payload = []
    for tool in response.tools:
        if tool.tool_name in tool_schemas:
            clean_args = sanitize_args(tool.tool_args, tool_schemas[tool.tool_name])
            selected_tools_payload.append({"name": tool.tool_name, "args": clean_args})

    # print(f"[DEBUG Tool Getter] Selected and validated tools: {selected_tools_payload}\n")

    return {
        "selected_tools": selected_tools_payload
    }