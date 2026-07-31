import os
from typing import cast
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.observability import observe
from app.agent.state import AgentState
from app.agent.llm import get_llm

class PlannerOutput(BaseModel):
    reasoning: str = Field(
        description="Short reason for the decision."
    )
    needs_tool: bool = Field(
        description="DEFAULT IS TRUE. Set to False STRICTLY ONLY for static definitions, trivia, or general text generation."
    )


llm = get_llm(0.0)
structured_llm = llm.with_structured_output(PlannerOutput)


SYSTEM_PROMPT = """You are a deterministic tool requirement classifier.

DEFAULT RULE:
Set needs_tool = True by default.

MANDATORY TOOL TRIGGERS (needs_tool = True):
- Help or capabilities requests (e.g., "help", "ayuda", "what can you do?").
- File, path, or directory operations (e.g., "notes.txt", "Downloads", "/home/user").
- Any action verb on disk or system state (e.g., list, read, search, create, delete).

EXEMPTION RULES (needs_tool = False STRICTLY ONLY IF):
- Pure conceptual definitions or general trivia (e.g., "What is Python?", "Is a 40kg dog heavy?").
- Casual greetings or pleasantries (e.g., "Hello", "How are you?").
- Pure in-memory text/code generation without saving or execution requests.

FEW-SHOT EXAMPLES:

User: "ayuda"
Reasoning: System capability request requiring tool invocation.
needs_tool: True

User: "What is Python?"
Reasoning: Pure conceptual definition query.
needs_tool: False

User: "Is a 40kg dog heavy?"
Reasoning: General knowledge trivia request.
needs_tool: False

User: "List files in Downloads"
Reasoning: Local directory inspection request.
needs_tool: True
"""


@observe(name="planner_node", as_type="chain")
def planner_node(state: AgentState) -> dict:
    """Planner Node: Evaluates user input and decides whether tools are required."""
    user_input = state["input"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    response = cast(PlannerOutput, structured_llm.invoke(messages))    
    
    return {
        "needs_tool": response.needs_tool,
        "planner_reasoning": response.reasoning
    }