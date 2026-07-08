"""Anthropic (Claude) provider. Requires the `anthropic` package and an API key."""

from __future__ import annotations

import os

from agentmesh.core.message import Message, Role
from agentmesh.providers.base import Provider


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        api_key: str | None = None,
        max_tokens: int = 1024,
    ):
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for AnthropicProvider. "
                "Install with: pip install agentmesh[anthropic]"
            ) from exc

        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def complete(self, messages: list[Message], **kwargs) -> str:
        system = "\n".join(m.content for m in messages if m.role == Role.SYSTEM)
        turns = [
            {"role": m.role.value, "content": m.content}
            for m in messages
            if m.role in (Role.USER, Role.ASSISTANT)
        ]
        response = self._client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            system=system or None,
            messages=turns,
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
