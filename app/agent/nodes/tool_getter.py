# app/agent/nodes/tool_getter.py
from typing import cast
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.mcp_adapter import get_mcp_tools

llm = get_llm(temperature=0.0)

SYSTEM_PROMPT = """You are the Tool Selection Module for SystemPilot.

Your job is to select the appropriate tool and populate its arguments matching its schema.

GENERAL DIRECTIVES:
1. ARGUMENT COMPLETENESS: Generate all required content/text inside tool arguments.
2. PATH RESOLUTION: When operating on items from a previous listing tool, construct the full absolute path by joining `target_directory` + `/` + `item.name` (e.g., `/home/user/Downloads/file.txt`). NEVER pass a directory path to a file-level tool like `delete_file`.
3. CONDITIONAL COMPLETION: If a previous tool output returned empty results (`items: []` or `total_items: 0`) and the task is conditional ("if present then delete"), DO NOT CALL ANY MORE TOOLS. Your work is done.
4. NO REPETITION OR RETRIES ON ERROR: Do NOT call the same tool with the exact same arguments if it has already been executed or returned an error in the history.
5. SEQUENTIAL EXECUTION: Return AT MOST ONE tool call per step.
"""

def format_history_for_getter(tool_results: list[dict]) -> str:
    formatted = []
    for item in tool_results:
        tool = item.get("tool")
        args = item.get("args")
        res = item.get("result") or item.get("error")
        formatted.append(f"Executed: {tool}(args={args})\nOutput:\n{res}\n")
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

    # Filter out tool calls that have already been executed
    executed_calls = {
        (item.get("tool"), str(item.get("args"))) 
        for item in tool_results
    }

    valid_tool_calls = []
    for tc in tool_calls:
        call_signature = (tc["name"], str(tc["args"]))
        if call_signature not in executed_calls:
            valid_tool_calls.append(tc)

    if len(valid_tool_calls) > 1:
        valid_tool_calls = valid_tool_calls[:1]

    selected_tools_payload = [
        {"name": tc["name"], "args": tc["args"]} 
        for tc in valid_tool_calls
    ]

    return {"selected_tools": selected_tools_payload}