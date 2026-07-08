"""A deterministic provider that requires no API key.

Used for tests, examples, and CI so the whole framework can be built and
verified on any machine without external credentials.
"""

from __future__ import annotations

from agentmesh.core.message import Message
from agentmesh.providers.base import Provider


class MockProvider(Provider):
    """Echoes a deterministic, templated response based on the last user message.

    Optionally accepts a `responses` mapping of substrings -> canned replies,
    so example workflows can produce readable, reproducible output.
    """

    name = "mock"

    def __init__(self, responses: dict[str, str] | None = None, default: str | None = None):
        self.responses = responses or {}
        self.default = default

    def complete(self, messages: list[Message], **kwargs) -> str:
        last_user = next((m for m in reversed(messages) if m.role.value == "user"), None)
        prompt = last_user.content if last_user else ""
        for key, reply in self.responses.items():
            if key.lower() in prompt.lower():
                return reply
        if self.default is not None:
            return self.default
        system = next((m for m in messages if m.role.value == "system"), None)
        persona = system.content if system else "agent"
        return f"[{persona}] Processed: {prompt[:120]}"
