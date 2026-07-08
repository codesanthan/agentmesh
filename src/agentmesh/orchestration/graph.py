"""TaskGraph: a DAG of tasks with dependency validation and topological ordering."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentmesh.core.task import Task


class GraphError(Exception):
    pass


@dataclass
class TaskGraph:
    tasks: dict[str, Task] = field(default_factory=dict)

    def add(self, task: Task) -> None:
        if task.id in self.tasks:
            raise GraphError(f"Duplicate task id '{task.id}'")
        self.tasks[task.id] = task

    def validate(self) -> None:
        for task in self.tasks.values():
            for dep in task.depends_on:
                if dep not in self.tasks:
                    raise GraphError(f"Task '{task.id}' depends on unknown task '{dep}'")
        self.topological_order()  # raises on cycles

    def topological_order(self) -> list[list[str]]:
        """Return task ids grouped into 'waves' that can run in parallel."""
        remaining = {tid: set(t.depends_on) for tid, t in self.tasks.items()}
        done: set[str] = set()
        waves: list[list[str]] = []

        while remaining:
            ready = sorted(tid for tid, deps in remaining.items() if deps <= done)
            if not ready:
                raise GraphError(f"Cycle detected among tasks: {sorted(remaining)}")
            waves.append(ready)
            for tid in ready:
                done.add(tid)
                del remaining[tid]
        return waves
