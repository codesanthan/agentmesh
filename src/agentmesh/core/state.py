"""Shared execution state (a 'blackboard') passed between agents during a run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentmesh.core.task import TaskResult


@dataclass
class ExecutionState:
    """Accumulates results and shared memory across a workflow run."""

    results: dict[str, TaskResult] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)

    def record(self, result: TaskResult) -> None:
        self.results[result.task_id] = result

    def output_of(self, task_id: str) -> str:
        result = self.results.get(task_id)
        if result is None:
            raise KeyError(f"No result recorded yet for task '{task_id}'")
        return result.output

    def context_for(self, depends_on: list[str]) -> str:
        """Build a text block summarizing the outputs of upstream tasks."""
        if not depends_on:
            return ""
        parts = []
        for dep_id in depends_on:
            result = self.results.get(dep_id)
            if result is not None:
                parts.append(f"[{dep_id}] {result.output}")
        return "\n\n".join(parts)
