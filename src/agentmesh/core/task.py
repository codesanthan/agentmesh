"""Task and TaskResult primitives representing a unit of work for an agent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agentmesh.core.usage import Usage


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


# A validator inspects a task's raw output and returns a human-readable
# failure reason if the output is unacceptable, or None if it's fine.
#
# This is the hook for catching a task that *returns* successfully from the
# provider but is still garbage -- an empty string, a refusal, a truncated
# answer. A bare try/except around the provider call can never see that kind
# of failure, because nothing raised.
Validator = Callable[[str], "str | None"]


@dataclass
class Task:
    id: str
    prompt: str
    agent: str
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 0
    validate: Validator | None = None


@dataclass
class TaskResult:
    task_id: str
    agent: str
    status: TaskStatus
    output: str = ""
    error: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    usage: Usage | None = None
    attempts: int = 1
