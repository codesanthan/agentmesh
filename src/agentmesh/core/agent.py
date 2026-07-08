"""The Agent: a persona bound to a provider, with an optional toolset."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentmesh.core.message import Message, Role
from agentmesh.providers.base import Provider
from agentmesh.tools.registry import ToolRegistry


@dataclass
class Agent:
    name: str
    provider: Provider
    system_prompt: str = "You are a helpful assistant."
    tools: ToolRegistry | None = None
    history: list[Message] = field(default_factory=list)

    def act(self, prompt: str, context: str = "") -> str:
        """Run one turn: build the message list, call the provider, record history."""
        full_prompt = f"{context}\n\n{prompt}".strip() if context else prompt
        messages = [
            Message(role=Role.SYSTEM, content=self.system_prompt, sender=self.name),
            *self.history,
            Message(role=Role.USER, content=full_prompt, sender=self.name),
        ]
        output = self.provider.complete(messages)
        self.history.append(Message(role=Role.USER, content=full_prompt, sender=self.name))
        self.history.append(Message(role=Role.ASSISTANT, content=output, sender=self.name))
        return output

    def use_tool(self, tool_name: str, **kwargs) -> str:
        if self.tools is None:
            raise RuntimeError(f"Agent '{self.name}' has no tools registered")
        return self.tools.invoke(tool_name, **kwargs)
