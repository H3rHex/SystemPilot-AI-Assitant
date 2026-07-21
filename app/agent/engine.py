from typing import Generator, Any
from openai import OpenAI
from app.agent.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME, LLM_STREAMING, SYSTEM_PROMPT
from app.agent.mcp_adapter import MCPAdapter
from app.agent.completion import CompletionHandler

class AgentEngine:
    """High-level LLM orchestrator for SystemPilot."""
    
    def __init__(self) -> None:
        self.base_url: str = LLM_BASE_URL or ""
        self.api_key: str = LLM_API_KEY or ""
        self.model_name: str = LLM_MODEL_NAME or ""
        self.use_streaming: bool = LLM_STREAMING if LLM_STREAMING is not None else False

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self.mcp = MCPAdapter()
        self.completion = CompletionHandler(self.client, self.model_name, self.mcp)

    def _has_valid_config(self) -> bool:
        """Validate presence of environment credentials."""
        return bool(self.api_key and self.base_url and self.model_name)

    def _build_context(self, prompt: str) -> list[dict[str, Any]]:
        """Construct the prompt message context."""
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

    def get_response(self, prompt: str) -> Generator[str, None, None]:
        """Orchestrate LLM text generation and MCP tool resolution."""
        if not self._has_valid_config():
            yield "[bold red]❌ Config Error:[/bold red] You must introduce your LLM credentials in the environment setup."
            return

        try:
            messages = self._build_context(prompt)
            tools = self.mcp.get_tools()

            if self.use_streaming:
                yield from self.completion.generate_stream(messages, tools)
            else:
                yield from self.completion.generate_static(messages, tools)

        except Exception as e:
            yield f"[bold red]❌ LLM Engine Error:[/bold red] {str(e)}"