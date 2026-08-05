# app/agent/nodes/response_writer.py
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm

llm = get_llm(temperature=0.15)

SYSTEM_PROMPT = """You are SystemPilot, a concise, helpful, and elegant local system administration assistant.

Your job is to provide the final answer to the user based on the executed plan.

GUIDELINES:
1. READ THE CONTEXT: You will receive the user's original request, the normalized goal, the facts discovered, and the tools executed.
2. BE CONCISE & ELEGANT: Provide direct, short, and professional answers. Summarize what was done in a human-friendly way without dumping raw JSON or code.
3. NO HALLUCINATIONS: Base your answer EXCLUSIVELY on the provided facts and tool results. Never invent, assume, or guess system data.
4. HANDLING FAILURES: If tools failed or the goal couldn't be met, explain gracefully what happened and why.
5. NO FALSE CONFIRMATIONS: NEVER state, imply, or confirm that an action (such as deleting, moving, or modifying files) was performed unless the corresponding tool (e.g., `delete_file`) actually appears executed with success in 'Tool Results'.
6. FAILURE TRANSPARENCY: If the execution stopped early or tools were not invoked, clearly inform the user about what steps were inspected and what actions remain unfulfilled. Never hallucinate completion.

Example successful response:
"I have successfully scanned your Downloads folder and deleted the 3 temporary text files as requested."

Example fallback response:
"I am currently unable to complete that action on your system due to a permission error."
"""

@observe(name="response_writer_node", as_type="generation")
async def response_writer_node(state: AgentState) -> dict:
    user_input = state["input"]
    goal = state.get("goal", "No specific goal recorded.")
    tool_results = state.get("tool_results", [])
    facts = state.get("facts", [])

    context_parts = [
        f"User Request: {user_input}",
        f"Normalized Goal: {goal}"
    ]
    
    if facts:
        clean_facts = [
            f"- {f.get('key')}: {f.get('value')}" 
            for f in facts 
            if f.get("source") in ("evaluator", "system")
        ]
        if clean_facts:
            context_parts.append("Discovered Facts:\n" + "\n".join(clean_facts))
            
    if tool_results:
        action_summary = []
        for tr in tool_results:
            name = tr.get("tool", "unknown_tool")
            if tr.get("error"):
                status = f"Failed ({tr.get('error')})"
            else:
                # Limitamos la longitud del resultado por si es gigante
                raw_res = str(tr.get("result", ""))
                res_preview = raw_res[:100] + "..." if len(raw_res) > 100 else raw_res
                status = f"Success (Output: {res_preview})"
            
            action_summary.append(f"- Used {name}: {status}")
            
        context_parts.append("Actions Taken:\n" + "\n".join(action_summary))

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="\n\n".join(context_parts))
    ]

    response = await llm.ainvoke(messages)

    return {
        "final_response": str(response.content),
        "phase": "done"
    }