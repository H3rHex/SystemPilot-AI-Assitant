# app/agent/nodes/fallback_node.py
from app.agent.observability import observe
from app.agent.state import AgentState

@observe(name="fallback_node", as_type="chain")
def fallback_node(state: AgentState) -> dict:
    """Fallback node to immediately return a static error response upon critical failure."""
    
    # Extraemos el error registrado, por defecto UNKNOWN_ERROR
    error_type = state.get("error") or "UNKNOWN_ERROR"
    
    # Diccionario con respuestas amigables para los errores conocidos
    error_messages = {
        "PLANNER_TIMEOUT": "The planning system took too long to respond. Please try simplifying your request.",
        "PLANNER_ERROR": "I encountered an internal error while trying to plan the task. Please try again.",
        "MAX_STEPS_REACHED": "The task took too many steps and was stopped to prevent an infinite loop. Some actions may have been partially completed.",
        "EVALUATOR_ERROR": "I had trouble evaluating the results of the actions taken. Please check the system state manually."
    }
    
    # Obtenemos el mensaje predefinido o un mensaje genérico con el código de error
    fallback_message = error_messages.get(
        error_type, 
        f"An unexpected system error occurred ({error_type}). Please try again."
    )

    # Devolvemos final_response (acorde al AgentState) y marcamos la fase como 'error'
    return {
        "final_response": fallback_message,
        "phase": "error"
    }