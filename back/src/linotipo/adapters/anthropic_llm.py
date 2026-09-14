"""LLM real sobre la API de Anthropic."""

from __future__ import annotations

from anthropic import Anthropic


class AnthropicLLM:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "claude-sonnet-5",
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> None:
        self._client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def complete(self, *, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
