"""Provider interface: anything that can turn a prompt + history into a completion."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentmesh.core.message import Message
from agentmesh.core.usage import Usage


class Provider(ABC):
    """Abstract base class for LLM backends."""

    name: str = "base"

    @abstractmethod
    def complete(self, messages: list[Message], **kwargs) -> str:
        """Return a text completion given a conversation history."""
        raise NotImplementedError

    def complete_with_usage(self, messages: list[Message], **kwargs) -> tuple[str, Usage]:
        """Like `complete`, but also return token/cost usage for the call.

        Providers that can report real usage (Anthropic, OpenAI) override
        this directly. The default implementation here falls back to
        `complete()` and reports zero usage, so any existing custom
        Provider subclass keeps working unchanged.
        """
        return self.complete(messages, **kwargs), Usage()
