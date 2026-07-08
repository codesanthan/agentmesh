"""Message primitives exchanged between agents and providers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: Role
    content: str
    sender: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "sender": self.sender,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
