# app/agent/nodes/tool_reviewer.py
from typing import Any, cast
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.config import MAX_TOOLS_PER_STEP

class ReviewerOutput(BaseModel):
    approved: bool = Field(
        description="True if the proposed tool sequence is safe, relevant, and correctly parametrized. False otherwise."
    )
    discard_tools: list[str] = Field(
        default_factory=list,
        description="List of tool names from the proposal that are inappropriate or failed validation."
    )
    reasoning: str = Field(
        description="Detailed reasoning for approving or rejecting the execution plan."
    )

llm = get_llm(temperature=0.0)
structured_llm = llm.with_structured_output(ReviewerOutput)

SYSTEM_PROMPT = """You are the Tool Reviewer and Safety Guardrail for SystemPilot.

Your task is to review the proposed sequence of tools and their parameters against the user's original request.

Validation Rules:
1. Ensure the selected tools are directly relevant to fulfilling the request.
2. Confirm that the arguments provided for each tool are logically sound and valid.
3. Reject execution if the tool sequence is nonsensical, redundant, or unsafe.
4. If rejecting due to unsuitable tools, explicitly populate `discard_tools` with their names.

ALWAYS respond using the required JSON schema."""

async def tool_reviewer_node(state: AgentState) -> dict:
    """Tool Reviewer Node: Validates proposed tools and enforces max retry limits."""
    user_input = state["input"]
    selected_tools = cast(list[dict[str, Any]], state.get("selected_tools", []))
    current_retries = state.get("retry_count", 0)
    
    # Si se alcanza el límite de reintentos, abortamos la evaluación de tools
    if current_retries >= MAX_TOOLS_PER_STEP:
        return {
            "is_approved": False,
            "reasoning": f"Reached maximum retry threshold ({MAX_TOOLS_PER_STEP}). Stopping tool evaluation loop.",
            "retry_count": current_retries
        }

    if not selected_tools:
        return {
            "is_approved": False,
            "reasoning": "No tools were provided for review.",
            "retry_count": current_retries
        }
        
    tools_summary = "\n".join(
        [f"- Tool: {t.get('name', '')} | Args: {t.get('args', {})}" for t in selected_tools]
    )
    
    user_content = f"User Input: {user_input}\n\nProposed Tool Sequence:\n{tools_summary}"
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]
    
    response = cast(ReviewerOutput, await structured_llm.ainvoke(messages))
    
    current_discarded = list(state.get("discarded_tools", []))
    new_retry_count = current_retries

    if not response.approved:
        new_retry_count += 1
        if response.discard_tools:
            for tool_name in response.discard_tools:
                if tool_name not in current_discarded:
                    current_discarded.append(tool_name)

    return {
        "is_approved": response.approved,
        "discarded_tools": current_discarded,
        "retry_count": new_retry_count
    }