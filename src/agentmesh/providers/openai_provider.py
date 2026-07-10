"""OpenAI provider. Requires the `openai` package and an API key."""

from __future__ import annotations

import os

from agentmesh.core.message import Message
from agentmesh.core.usage import Usage
from agentmesh.providers.base import Provider

# Approximate list pricing in USD per 1M tokens, as (input, output). This is
# a best-effort estimate for cost *tracking*, not billing -- check
# https://openai.com/api/pricing for current rates. Keys are checked as
# substrings of the model name, most specific first.
PRICING_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def _price_for(model: str) -> tuple[float, float] | None:
    for key, price in PRICING_PER_MILLION_TOKENS.items():
        if key in model:
            return price
    return None


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
        return self.complete_with_usage(messages, **kwargs)[0]

    def complete_with_usage(self, messages: list[Message], **kwargs) -> tuple[str, Usage]:
        turns = [{"role": m.role.value, "content": m.content} for m in messages]
        model = kwargs.get("model", self.model)
        response = self._client.chat.completions.create(model=model, messages=turns)
        text = response.choices[0].message.content or ""

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        price = _price_for(model)
        cost_usd = (
            (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000 if price else 0.0
        )
        return text, Usage(
            input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd
        )
