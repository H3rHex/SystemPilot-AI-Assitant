from typing import TypedDict, Any, Literal


class FactEntry(TypedDict, total=False):
    key: str
    value: str | int | float | bool | dict[str, Any] | list[Any] | None
    type: str
    source: str
    metadata: dict[str, Any]


class ToolResultEntry(TypedDict, total=False):
    tool: str
    args: dict[str, Any]
    result: str | dict[str, Any] | list[Any] | None
    error: str | None


class AgentState(TypedDict):
    input: str

    phase: Literal[
        "idle",
        "plan",
        "inspect",
        "evaluate_results",
        "finalize",
        "done",
        "error"
    ]

    goal: str | None
    context: dict[str, Any]
    facts: list[FactEntry]
    working_memory: dict[str, Any]

    needs_tool: bool
    needs_another_tool: bool
    next_tool_step_count: int

    last_tool_name: str | None
    last_tool_args: dict[str, Any]

    selected_tools: list[dict[str, Any]]
    tool_results: list[ToolResultEntry]

    final_response: str
    error: str | None