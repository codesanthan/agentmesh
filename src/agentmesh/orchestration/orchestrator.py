"""Orchestrator: executes a TaskGraph against a pool of agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentmesh.core.agent import Agent
from agentmesh.core.state import ExecutionState
from agentmesh.core.task import Task, TaskResult, TaskStatus
from agentmesh.orchestration.graph import TaskGraph
from agentmesh.orchestration.strategies import Strategy, run_wave_parallel, run_wave_sequential


class OrchestratorError(Exception):
    pass


@dataclass
class Orchestrator:
    agents: dict[str, Agent]
    strategy: Strategy = Strategy.SEQUENTIAL
    supervisor: str | None = None
    state: ExecutionState = field(default_factory=ExecutionState)

    def run(self, graph: TaskGraph) -> ExecutionState:
        graph.validate()
        if self.strategy == Strategy.SUPERVISOR and not self.supervisor:
            raise OrchestratorError(
                "strategy='supervisor' requires an orchestrator.supervisor agent name"
            )

        waves = graph.topological_order()

        def run_one(task_id: str) -> None:
            self._run_task(graph.tasks[task_id])

        for wave in waves:
            if self.strategy == Strategy.PARALLEL:
                run_wave_parallel(wave, run_one)
            else:
                run_wave_sequential(wave, run_one)

        if self.strategy == Strategy.SUPERVISOR:
            self._run_supervisor_synthesis()

        return self.state

    def _run_task(self, task: Task) -> None:
        agent = self.agents.get(task.agent)
        if agent is None:
            self.state.record(
                TaskResult(
                    task_id=task.id,
                    agent=task.agent,
                    status=TaskStatus.FAILED,
                    error=f"Unknown agent '{task.agent}'",
                )
            )
            return
        try:
            context = self.state.context_for(task.depends_on)
            output = agent.act(task.prompt, context=context)
            self.state.record(
                TaskResult(
                    task_id=task.id,
                    agent=task.agent,
                    status=TaskStatus.SUCCEEDED,
                    output=output,
                )
            )
        except Exception as exc:  # noqa: BLE001 - surfaced via TaskResult, not swallowed
            self.state.record(
                TaskResult(
                    task_id=task.id,
                    agent=task.agent,
                    status=TaskStatus.FAILED,
                    error=str(exc),
                )
            )

    def _run_supervisor_synthesis(self) -> None:
        supervisor = self.agents[self.supervisor]
        summary = "\n\n".join(
            f"[{tid}] ({result.status.value}) {result.output or result.error}"
            for tid, result in self.state.results.items()
        )
        synthesis = supervisor.act(
            "Synthesize the results of the team's work below into a single final answer.",
            context=summary,
        )
        self.state.record(
            TaskResult(
                task_id="__supervisor_synthesis__",
                agent=self.supervisor,
                status=TaskStatus.SUCCEEDED,
                output=synthesis,
            )
        )
