# app/agent/nodes/reviewer.py
from typing import cast
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.config import MAX_DRAFT_PER_STEP

class FinalReviewerOutput(BaseModel):
    is_approved: bool = Field(
        description="True if the draft response is accurate, complete, and directly answers the user's input. False if it needs revision."
    )
    feedback: str = Field(
        description="Constructive critique explaining what needs fixing if not approved, or approval confirmation."
    )
    revised_response: str = Field(
        default="",
        description="Optional polished/corrected version of the final response if minor adjustments were needed."
    )

llm = get_llm(temperature=0.0)
structured_llm = llm.with_structured_output(FinalReviewerOutput)

SYSTEM_PROMPT = """You are the Final Quality Inspector for SystemPilot.

Your task is to inspect the draft response prepared for the user and ensure high quality and accuracy.

Validation Checklist:
1. Does the response directly answer the user's original query?
2. Is the response faithful to the tool results (no hallucinated data or false statements)?
3. Is the language clear, accurate, and free of technical jargon leaks?

If the draft is acceptable (even with minor flaws), approve it (`is_approved: True`). If you make minor polishing edits, place the finalized text in `revised_response`.
ALWAYS respond using the required JSON schema."""

async def reviewer_node(state: AgentState) -> dict:
    """Reviewer Node: Validates and approves the final response before sending it to the user."""
    user_input = state["input"]
    draft_response = state.get("draft_response", "")
    tool_results = state.get("tool_results", [])
    current_retries = state.get("draft_retry_count", 0)

    if current_retries >= MAX_DRAFT_PER_STEP:
        return {
            "is_final_approved": True,
            "final_response": draft_response,
            "reviewer_feedback": f"Forced approval: Reached maximum response retry limit ({MAX_DRAFT_PER_STEP}).",
            "response_retry_count": current_retries
        }

    context_content = (
        f"Original User Input: {user_input}\n"
        f"Tool Results Used: {tool_results}\n"
        f"Draft Response to Review: {draft_response}"
    )
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context_content)
    ]
    
    response = cast(FinalReviewerOutput, await structured_llm.ainvoke(messages))
    
    # Determine final response string
    final_output = response.revised_response if response.revised_response else draft_response

    return {
        "is_final_approved": response.is_approved,
        "final_response": final_output,
        "reviewer_feedback": response.feedback
    }