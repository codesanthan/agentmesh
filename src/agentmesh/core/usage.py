"""Token usage and cost accounting for a single provider call."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Usage:
    """Tokens and estimated cost for one `provider.complete_with_usage()` call.

    Cost is a best-effort estimate from a small built-in pricing table per
    provider -- treat it as directional, not a bill. Providers that can't
    compute a real cost (mock, or an unlisted model) report `cost_usd=0.0`
    rather than guessing.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
        )
