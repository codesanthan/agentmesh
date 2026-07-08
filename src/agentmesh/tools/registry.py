"""A simple registry that agents use to look up and invoke tools by name."""

from __future__ import annotations

from typing import Any

from agentmesh.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool '{name}'. Registered tools: {list(self._tools)}")
        return self._tools[name]

    def invoke(self, name: str, **kwargs: Any) -> str:
        return self.get(name).run(**kwargs)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools)
