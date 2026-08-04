# app/agent/engine.py
import asyncio
import warnings
from typing import Generator
from app.agent.graph import app_graph
from app.agent.observability import observe
from app.agent.state import AgentState

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

class AgentEngine:
    """High-level orchestrator for SystemPilot using LangGraph with clean token streaming."""

    @observe(name="systempilot.get_response", as_type="agent")
    def get_response(self, prompt: str) -> Generator[str, None, None]:
        """Orchestrates graph execution, yielding clean status updates and live final text tokens."""
        initial_state: AgentState = {
            "input": prompt,
            "needs_tool": False,
            "needs_another_tool": False,
            "next_tool_step_count": 0,
            "selected_tools": [],
            "tool_results": [],
            "final_response": "",
            "error":""
        }

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _run_graph_events():
                async for event in app_graph.astream_events(initial_state, version="v2"):
                    kind = event["event"]
                    name = event.get("name", "")

                    if kind == "on_chain_end" and name in ["planner", "tool_getter", "tool_runner","fallback_node"]:
                        output = event["data"].get("output", {})

                        if name == "planner":
                            needs_tool = output.get("needs_tool", False)
                            if needs_tool:
                                yield "[dim][[italic]Processing[/italic]] Analyzing request...[/dim]\n"

                        elif name == "tool_getter":
                            tools = output.get("selected_tools", [])
                            if tools:
                                tool_count = len(tools)
                                label = "tool" if tool_count == 1 else "tools"
                                yield f"[dim][[italic]Tools[/italic]] Selecting required {label}...[/dim]\n"

                        elif name == "tool_runner":
                            results = output.get("tool_results", [])
                            if results:
                                yield "[dim][[italic]Execution[/italic]] Fetching system data...[/dim]\n"

                        elif name == "fallback_node":
                            fallback_msg = output.get("final_response") or output.get("output") or "An unexpected error occurred."
                            yield f"[dim][bold red]{fallback_msg}[/bold red][/dim]\n"

                    # Only stream LLM tokens emitted inside the response_writer node
                    elif kind == "on_chat_model_stream":
                        metadata = event.get("metadata", {})
                        node_name = metadata.get("langgraph_node", "")

                        if node_name == "response_writer":
                            chunk = event["data"].get("chunk")
                            if chunk and hasattr(chunk, "content") and chunk.content:
                                yield chunk.content

            async_gen = _run_graph_events()
            try:
                while True:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    yield chunk
            except StopAsyncIteration:
                pass
            finally:
                loop.close()

        except Exception as e:
            yield f"[bold red]LangGraph Engine Error:[/bold red] {str(e)}"