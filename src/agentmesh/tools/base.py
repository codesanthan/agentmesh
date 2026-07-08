"""Tool interface: a callable an agent can invoke by name with keyword args."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    name: str
    description: str = ""

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        raise NotImplementedError
