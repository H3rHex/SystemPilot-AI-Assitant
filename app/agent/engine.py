from typing import Generator
from openai import OpenAI
from app.agent.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME, LLM_STREAMING, SYSTEM_PROMPT

class AgentEngine:
    def __init__(self) -> None:
        self.base_url: str = LLM_BASE_URL or ""
        self.api_key: str = LLM_API_KEY or ""
        self.model_name: str = LLM_MODEL_NAME or ""
        self.use_streaming: bool = LLM_STREAMING if LLM_STREAMING is not None else False

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def _has_valid_config(self) -> bool:
        """Check if all required LLM credentials are present."""
        return bool(self.api_key and self.base_url and self.model_name)

    def _build_context(self, prompt: str) -> list[dict[str, str]]:
        """Construct the message history for the API call."""
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

    def _generate_stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """Handle the streaming API call and yield tokens."""
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages, # type: ignore
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def _generate_static(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """Handle the blocking API call and yield the entire response at once."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages, # type: ignore
            stream=False
        )
        yield response.choices[0].message.content or ""

    def get_response(self, prompt: str) -> Generator[str, None, None]:
        """Orchestrate the LLM interaction based on configuration."""
        if not self._has_valid_config():
            yield "[bold red]❌ Config Error:[/bold red] You must introduce your LLM credentials in the environment setup."
            return
            
        try:
            messages = self._build_context(prompt)

            if self.use_streaming:
                yield from self._generate_stream(messages)
            else:
                yield from self._generate_static(messages)
                
        except Exception as e:
            yield f"[bold red]❌ LLM Engine Error:[/bold red] {str(e)}"