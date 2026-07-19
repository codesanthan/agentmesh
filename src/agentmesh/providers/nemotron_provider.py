"""NVIDIA Nemotron provider, via the OpenAI-compatible NVIDIA API Catalog endpoint.

Requires the `openai` package and an NVIDIA API key (https://build.nvidia.com).
"""

from __future__ import annotations

import os

from agentmesh.core.message import Message
from agentmesh.core.usage import Usage
from agentmesh.providers.base import Provider

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NemotronProvider(Provider):
    name = "nemotron"

    def __init__(
        self,
        model: str = "nvidia/nemotron-3-ultra-550b-a55b",
        api_key: str | None = None,
        base_url: str = NVIDIA_BASE_URL,
        max_tokens: int = 16384,
        temperature: float = 1,
        top_p: float = 0.95,
        enable_thinking: bool = True,
        reasoning_budget: int = 16384,
        price_per_million_tokens: tuple[float, float] | None = None,
    ):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for NemotronProvider (the NVIDIA "
                "API Catalog endpoint is OpenAI-compatible). Install with: "
                "pip install agentmesh[openai]"
            ) from exc

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.enable_thinking = enable_thinking
        self.reasoning_budget = reasoning_budget
        self.price_per_million_tokens = price_per_million_tokens
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key or os.environ.get("NVIDIA_API_KEY"),
        )

    def complete(self, messages: list[Message], **kwargs) -> str:
        return self.complete_with_usage(messages, **kwargs)[0]

    def complete_with_usage(self, messages: list[Message], **kwargs) -> tuple[str, Usage]:
        turns = [{"role": m.role.value, "content": m.content} for m in messages]
        model = kwargs.get("model", self.model)

        stream = self._client.chat.completions.create(
            model=model,
            messages=turns,
            temperature=kwargs.get("temperature", self.temperature),
            top_p=kwargs.get("top_p", self.top_p),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            extra_body={
                "chat_template_kwargs": {"enable_thinking": self.enable_thinking},
                "reasoning_budget": self.reasoning_budget,
            },
            stream=True,
            stream_options={"include_usage": True},
        )

        content_parts: list[str] = []
        input_tokens = 0
        output_tokens = 0
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens or 0
                output_tokens = chunk.usage.completion_tokens or 0

        text = "".join(content_parts)
        # NVIDIA API Catalog pricing isn't published in a stable, checkable
        # form here -- report real token counts and, unless the caller
        # supplies price_per_million_tokens, $0.00 cost rather than guessing.
        cost_usd = 0.0
        if self.price_per_million_tokens is not None:
            in_price, out_price = self.price_per_million_tokens
            cost_usd = (input_tokens * in_price + output_tokens * out_price) / 1_000_000
        return text, Usage(
            input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd
        )
