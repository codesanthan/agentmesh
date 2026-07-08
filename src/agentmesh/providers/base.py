"""Provider interface: anything that can turn a prompt + history into a completion."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentmesh.core.message import Message


class Provider(ABC):
    """Abstract base class for LLM backends."""

    name: str = "base"

    @abstractmethod
    def complete(self, messages: list[Message], **kwargs) -> str:
        """Return a text completion given a conversation history."""
        raise NotImplementedError
