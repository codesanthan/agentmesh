"""A deterministic provider that requires no API key.

Used for tests, examples, and CI so the whole framework can be built and
verified on any machine without external credentials.
"""

from __future__ import annotations

from agentmesh.core.message import Message
from agentmesh.core.usage import Usage
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
        return self.complete_with_usage(messages, **kwargs)[0]

    def complete_with_usage(self, messages: list[Message], **kwargs) -> tuple[str, Usage]:
        last_user = next((m for m in reversed(messages) if m.role.value == "user"), None)
        prompt = last_user.content if last_user else ""

        output = None
        for key, reply in self.responses.items():
            if key.lower() in prompt.lower():
                output = reply
                break
        if output is None:
            if self.default is not None:
                output = self.default
            else:
                system = next((m for m in messages if m.role.value == "system"), None)
                persona = system.content if system else "agent"
                output = f"[{persona}] Processed: {prompt[:120]}"

        # Word-count is a free, deterministic stand-in for a real tokenizer --
        # good enough to demonstrate the usage-reporting mechanism without a
        # tokenizer dependency. Cost is always $0: mock calls never touch a
        # real API.
        input_tokens = sum(len(m.content.split()) for m in messages)
        output_tokens = len(output.split())
        usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=0.0)
        return output, usage
