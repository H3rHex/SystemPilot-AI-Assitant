from typing import Any, cast
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools

class ToolCall(BaseModel):
    tool_name: str = Field(
        description="The exact name of the selected tool."
    )
    tool_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary containing arguments matching the tool's schema."
    )


class ToolSelectionOutput(BaseModel):
    tools: list[ToolCall] = Field(
        default_factory=list,
        description="Ordered list of tools required to satisfy the user's request. Empty if no tools fit."
    )
    reasoning: str = Field(
        description="Explanation of why these specific tools and sequence were selected."
    )



llm = get_llm(temperature=0.0)
structured_llm = llm.with_structured_output(ToolSelectionOutput)

SYSTEM_PROMPT = """You are the Tool Selection Module for SystemPilot.

Your task is to analyze the user's request and select ALL necessary tools from the provided catalog required to fulfill the task.

Rules:
1. You can select ONE OR MORE tools. Order them in the exact logical execution sequence.
2. You MUST select tools ONLY from the AVAILABLE TOOLS list below.
3. Do NOT select tools that are explicitly marked as DISCARDED.
4. Extract and provide all required arguments strictly conforming to each tool's expected schema.
5. If no available tool matches the user's intent, return an empty tools list `[]`.

AVAILABLE TOOLS:
{tools_schema}

DISCARDED TOOLS (DO NOT USE):
{discarded_tools}
"""

async def tool_getter_node(state: AgentState) -> dict:
    """Tool Getter Node: Selects one or multiple MCP tools asynchronously."""
    user_input = state["input"]
    discarded = state.get("discarded_tools", [])
    
    all_tools = await get_mcp_tools()
    
    available_tools = [t for t in all_tools if t["name"] not in discarded]
    
    tools_str = "\n".join([f"- {t['name']}: {t['description']} (Args: {t.get('inputSchema', {})})" for t in available_tools])
    discarded_str = ", ".join(discarded) if discarded else "None"
    
    formatted_system_prompt = SYSTEM_PROMPT.format(
        tools_schema=tools_str,
        discarded_tools=discarded_str
    )
    
    messages = [
        SystemMessage(content=formatted_system_prompt),
        HumanMessage(content=user_input)
    ]
    
    response = cast(ToolSelectionOutput, await structured_llm.ainvoke(messages))
    
    selected_tools_payload = [
        {"name": tool.tool_name, "args": tool.tool_args}
        for tool in response.tools
        if tool.tool_name
    ]

    return {
        "selected_tools": selected_tools_payload
    }
