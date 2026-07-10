"""Anthropic (Claude) provider. Requires the `anthropic` package and an API key."""

from __future__ import annotations

import os

from agentmesh.core.message import Message, Role
from agentmesh.core.usage import Usage
from agentmesh.providers.base import Provider

# Approximate list pricing in USD per 1M tokens, as (input, output). This is
# a best-effort estimate for cost *tracking*, not billing -- check
# https://www.anthropic.com/pricing for current rates. Keys are checked as
# substrings of the model name, most specific first.
PRICING_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "claude-opus-4": (15.00, 75.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-haiku": (0.80, 4.00),
}


def _price_for(model: str) -> tuple[float, float] | None:
    for key, price in PRICING_PER_MILLION_TOKENS.items():
        if key in model:
            return price
    return None


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
        return self.complete_with_usage(messages, **kwargs)[0]

    def complete_with_usage(self, messages: list[Message], **kwargs) -> tuple[str, Usage]:
        system = "\n".join(m.content for m in messages if m.role == Role.SYSTEM)
        turns = [
            {"role": m.role.value, "content": m.content}
            for m in messages
            if m.role in (Role.USER, Role.ASSISTANT)
        ]
        model = kwargs.get("model", self.model)
        response = self._client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            system=system or None,
            messages=turns,
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        price = _price_for(model)
        cost_usd = (
            (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000 if price else 0.0
        )
        return text, Usage(
            input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd
        )
