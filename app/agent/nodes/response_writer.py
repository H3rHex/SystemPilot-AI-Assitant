# app/agent/nodes/response_writer.py
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm

llm = get_llm(temperature=0.15)

SYSTEM_PROMPT = """You are SystemPilot, a concise local system administration assistant.

GUIDELINES:
1. BE CONCISE: Provide direct, short, and professional answers. Avoid unnecessary filler or lengthy explanations.
2. NO HALLUCINATIONS: Base your answer EXCLUSIVELY on the provided tool results. Never invent, assume, or guess system data.
3. HANDLING FAILURES OR MISSING DATA: If a tool failed, returned empty output, or lacks the capability to get the requested information, state clearly and politely that you cannot retrieve it right now.

Example fallback response:
"I am currently unable to retrieve that information from your system."
"""

@observe(name="response_writer_node", as_type="generation")
async def response_writer_node(state: AgentState) -> dict:
    user_input = state["input"]
    tool_results = state.get("tool_results", [])

    context_parts = [f"User Request: {user_input}"]
    
    if tool_results:
        context_parts.append(f"Tool Execution Results:\n{tool_results}")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="\n\n".join(context_parts))
    ]

    response = await llm.ainvoke(messages)

    return {"final_response": str(response.content)}