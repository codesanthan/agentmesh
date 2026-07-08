"""OpenAI provider. Requires the `openai` package and an API key."""

from __future__ import annotations

import os

from agentmesh.core.message import Message
from agentmesh.providers.base import Provider


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for OpenAIProvider. "
                "Install with: pip install agentmesh[openai]"
            ) from exc

        self.model = model
        self._client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def complete(self, messages: list[Message], **kwargs) -> str:
        turns = [{"role": m.role.value, "content": m.content} for m in messages]
        response = self._client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=turns,
        )
        return response.choices[0].message.content or ""
