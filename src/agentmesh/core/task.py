"""Task and TaskResult primitives representing a unit of work for an agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    id: str
    prompt: str
    agent: str
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    agent: str
    status: TaskStatus
    output: str = ""
    error: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
