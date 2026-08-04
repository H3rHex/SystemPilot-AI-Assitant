# app/agent/nodes/tool_getter.py
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools

llm = get_llm(temperature=0.0)

SYSTEM_PROMPT = """You are the Tool Selection Module for SystemPilot.

Your job is to select the appropriate tool(s) and populate their arguments strictly matching their defined input schemas.

GENERAL DIRECTIVES:
1. ARGUMENT COMPLETENESS: If a tool requires content, text, or query generation, GENERATE the full required content inside the appropriate tool argument.
2. CONTEXTUAL REUSE: Read the previous tool execution results carefully. Use extracted file names, paths, or IDs to execute subsequent actions.
3. SCHEMA STRICTNESS: Only pass arguments defined in the tool's input schema. Do not invent extra parameters.
4. SEQUENTIAL EXECUTION: Return ONLY ONE tool call per step if subsequent actions depend on previous outputs.
5. NO DUPLICATES: Do NOT call the same tool with identical arguments if it has already succeeded in the history. Move to the next logical action required by the user request.
6. IGNORE NOISY MCP METADATA: Do not consider internal cache, annotations, SDK wrappers, or debug noise. Only use the user-relevant result summary.
"""


def format_history_for_getter(tool_results: list[dict[str, Any]]) -> str:
    recent = tool_results[-3:]
    formatted = []
    for item in recent:
        tool = item.get("tool")
        args = item.get("args")
        res = item.get("result") or item.get("error") or ""
        result_text = str(res).strip()
        if len(result_text) > 900:
            result_text = result_text[:900] + "..."
        formatted.append(f"Tool Executed: {tool}(args={args})\nResult:\n{result_text}\n")
    return "\n---\n".join(formatted)


@observe(name="tool_getter_node", as_type="chain")
async def tool_getter_node(state: AgentState) -> dict:
    user_input = state["input"]
    discarded = state.get("discarded_tools", [])
    tool_results = state.get("tool_results", [])

    all_tools = await get_mcp_tools()
    available_tools = [t for t in all_tools if t["name"] not in discarded]

    llm_with_tools = llm.bind_tools(available_tools)

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    if tool_results:
        history_text = format_history_for_getter(tool_results)
        messages.append(HumanMessage(
            content=f"Original Request: {user_input}\n\nExecuted Tools History:\n{history_text}"
        ))
    else:
        messages.append(HumanMessage(content=f"User Request: {user_input}"))

    response = await llm_with_tools.ainvoke(messages)

    tool_calls = response.tool_calls or []

    if len(tool_calls) > 1:
        tool_calls = tool_calls[:1]

    selected_tools_payload = [
        {"name": tc["name"], "args": tc["args"]}
        for tc in tool_calls
    ]

    return {"selected_tools": selected_tools_payload}