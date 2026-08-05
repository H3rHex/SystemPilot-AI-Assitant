import asyncio
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agent.config import LLM_TIMEOUT
from app.agent.llm import get_llm
from app.agent.observability import observe
from app.agent.state import AgentState

class EvaluatorOutput(BaseModel):
    reasoning: str = Field(
        description="Brief reasoning on whether the main goal is achieved based on the latest tool results."
    )
    goal_met: bool = Field(
        description="True ONLY if the original goal is completely fulfilled. False otherwise."
    )
    extracted_facts: list[dict[str, str]] = Field(
        description="List of new facts discovered (e.g., {'key': 'found_files', 'value': 'file1.txt, file2.txt'}). Empty list if nothing new.",
        default_factory=list
    )
    new_pending_targets: list[str] = Field(
        description="List of specific paths, filenames, or IDs that need subsequent actions. Empty if none.",
        default_factory=list
    )

llm = get_llm(0.0)
structured_llm = llm.with_structured_output(EvaluatorOutput)

SYSTEM_PROMPT = """You are the Result Evaluator for an AI agent.
Your job is to read the latest tool execution result and decide if the user's primary GOAL has been met.

RULES:
1. Compare the GOAL against the actual output of the last executed tool.
2. If the goal requires acting on multiple items (e.g., 'delete all txt files'), and you just found the files, the goal is NOT met yet (you must return them in new_pending_targets).
3. If the tool returned an error, the goal is likely NOT met, unless it's a safe failure.
4. Extract any useful persistent information into 'extracted_facts'.
5. If further action is needed on specific items, list them in 'new_pending_targets'.
6. STRICT GOAL MATCHING: Evaluate tool results strictly against the exact literal text of the GOAL. 
7. NO INFERRED FILTERS: You are strictly forbidden from inventing filters(e.g., assuming only '.txt' files), naming patterns, or conditions not explicitly stated in the GOAL.
8. TARGET EXTRACTION: If the GOAL requests acting on multiple items (e.g., 'delete files in directory') and `list_directory` returned items, extract ALL eligible items into `new_pending_targets`.
"""

@observe(name="next_tool_step_evaluator", as_type="chain")
async def next_tool_step_evaluator(state: AgentState, config: RunnableConfig | None = None) -> dict:
    goal = state.get("goal", "Unknown goal")
    tool_results = state.get("tool_results", [])
    current_facts = state.get("facts", [])
    working_memory = state.get("working_memory", {}) or {}
    pending_targets = working_memory.get("pending_targets", [])
    step_count = state.get("next_tool_step_count", 0)
    
    if step_count >= 10:
        return {
            "phase": "finalize",
            "error": "MAX_STEPS_REACHED"
        }

    if not tool_results:
        return {"phase": "finalize"}

    last_result = tool_results[-1]
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"GOAL: {goal}\n\n"
                f"LAST TOOL EXECUTED: {last_result.get('tool')}\n"
                f"ARGS USED: {last_result.get('args')}\n"
                f"RESULT OUTPUT:\n{last_result.get('result') or last_result.get('error')}\n\n"
                f"CURRENT PENDING TARGETS: {pending_targets}"
            )
        )
    ]

    configurable = config.get("configurable", {}) if config else {}
    timeout_seconds = configurable.get("evaluator_timeout", LLM_TIMEOUT)

    try:
        response = await asyncio.wait_for(
            structured_llm.ainvoke(messages),
            timeout=float(timeout_seconds),
        )
        response = cast(EvaluatorOutput, response)

        new_facts = current_facts.copy()
        for fact in response.extracted_facts:
            new_facts.append({
                "key": fact.get("key", "unknown"),
                "value": fact.get("value", ""),
                "type": "string",
                "source": "evaluator",
                "metadata": {}
            })

        updated_targets = response.new_pending_targets
        if not updated_targets and pending_targets:
            updated_targets = pending_targets[1:] # Dequeue the first target if no new ones are added, assuming it was processed.

        if response.goal_met or (not updated_targets and not response.new_pending_targets and last_result.get("tool") != "list_directory"):
            next_phase = "finalize"
        else:
            # If there are still pending targets or new ones, we continue to the next tool execution phase.
            next_phase = "execute" if updated_targets else "inspect"

        return {
            "phase": next_phase,
            "facts": new_facts,
            "working_memory": {
                **working_memory,
                "pending_targets": updated_targets,
                "evaluator_reasoning": response.reasoning
            }
        }

    except Exception as e:
        return {
            "phase": "finalize",
            "error": f"EVALUATOR_ERROR: {str(e)}"
        }