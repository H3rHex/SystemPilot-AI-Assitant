from typing import TypedDict, Annotated, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """Global graph state, shared with all nodes"""

    input:str # Original user input
    messages:list[BaseMessage] # Message history
    
    needs_tool:bool 
    selected_tools: dict[str, Any] | None # Ai model selected tool list
    discarded_tools: list[str] # Rejected tools --> (when the selected tool is not suitable for the purpose)

    tool_result: str | None # MCP Server tool response
    draft_response: str # Draft node, generated text
    final_response:str # Final response text

    tool_retry_count:int # Prevent the model from entering a loop by choosing the right tool
    draft_retry_count:int # Prevent the model from entering a loop by making a good response