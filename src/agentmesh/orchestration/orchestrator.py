"""Orchestrator: executes a TaskGraph against a pool of agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentmesh.core.agent import Agent
from agentmesh.core.state import ExecutionState
from agentmesh.core.task import Task, TaskResult, TaskStatus
from agentmesh.core.usage import Usage
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

        # A task never runs on a partial or corrupted picture of its
        # dependencies. If any upstream task didn't succeed (whether it
        # failed outright or was itself skipped), skip this one too instead
        # of silently handing it a blank context and letting bad state
        # cascade further downstream.
        blocking = [dep for dep in task.depends_on if not self.state.succeeded(dep)]
        if blocking:
            self.state.record(
                TaskResult(
                    task_id=task.id,
                    agent=task.agent,
                    status=TaskStatus.SKIPPED,
                    error=(
                        "skipped: upstream dependency(ies) did not succeed: "
                        + ", ".join(blocking)
                    ),
                )
            )
            return

        max_attempts = task.max_retries + 1
        total_usage = Usage()
        last_error: str | None = None

        for attempt in range(1, max_attempts + 1):
            context = self.state.context_for(task.depends_on)
            if attempt > 1 and last_error:
                context = (
                    f"{context}\n\n[Retry {attempt - 1} feedback: the previous attempt "
                    f"failed because: {last_error}. Correct this and try again.]"
                ).strip()

            try:
                output, usage = agent.act_with_usage(task.prompt, context=context)
            except Exception as exc:  # noqa: BLE001 - surfaced via TaskResult, not swallowed
                last_error = str(exc)
                continue

            total_usage = total_usage + usage
            reason = task.validate(output) if task.validate is not None else None
            if reason is None:
                self.state.record(
                    TaskResult(
                        task_id=task.id,
                        agent=task.agent,
                        status=TaskStatus.SUCCEEDED,
                        output=output,
                        usage=total_usage,
                        attempts=attempt,
                    )
                )
                return
            last_error = reason

        self.state.record(
            TaskResult(
                task_id=task.id,
                agent=task.agent,
                status=TaskStatus.FAILED,
                error=last_error or "task failed with no error detail",
                usage=total_usage,
                attempts=max_attempts,
            )
        )

    def _run_supervisor_synthesis(self) -> None:
        supervisor = self.agents[self.supervisor]
        summary = "\n\n".join(
            f"[{tid}] ({result.status.value}) {result.output or result.error}"
            for tid, result in self.state.results.items()
        )
        synthesis, usage = supervisor.act_with_usage(
            "Synthesize the results of the team's work below into a single final answer.",
            context=summary,
        )
        self.state.record(
            TaskResult(
                task_id="__supervisor_synthesis__",
                agent=self.supervisor,
                status=TaskStatus.SUCCEEDED,
                output=synthesis,
                usage=usage,
            )
        )
