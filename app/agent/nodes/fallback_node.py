from app.agent.observability import observe
from app.agent.state import AgentState

@observe(name="fallback_node", as_type="chain")
def fallback_node(state: AgentState) -> dict:
    """Fallback node to immediately return a static error response upon critical failure."""
    error_type = state.get("error", "UNKNOWN_ERROR")
    
    # Pre-recorded static responses based on error type
    if error_type == "PLANNER_TIMEOUT":
        fallback_message = "The planning system timed out. Please try your request again."
    else:
        fallback_message = "An unexpected error occurred while processing your request."

    return {
        "output": fallback_message,
        "planner_reasoning": f"Execution halted due to {error_type}"
    }