# Architecture

## Design principles

**The provider boundary is sacred.** Every LLM call goes through
`Provider.complete(messages) -> str`. Orchestration, graph validation, and
agent state management never know or care which model answered. This is what
lets `MockProvider` stand in for Claude or GPT in tests, examples, and CI —
the same workflow YAML that hits a real model in production runs
deterministically and for free in a pull request check.

**Failures are data, not exceptions.** A task that raises is caught by the
orchestrator and recorded as a `TaskResult` with `status=FAILED` and an
`error` string. A single bad task doesn't crash a 20-task workflow; the
orchestrator finishes the run and the caller decides what "failed" means for
their use case (retry, skip, alert).

**The graph is explicit.** Dependencies between tasks (`depends_on`) are data,
not control flow buried in a script. `TaskGraph.topological_order()` turns
that data into "waves" of tasks that can run concurrently — which is also
what makes the `parallel` strategy possible without every workflow author
reasoning about threads.

## Execution strategies

| Strategy     | Behavior                                                                 | When to use                                              |
|--------------|---------------------------------------------------------------------------|-----------------------------------------------------------|
| `sequential` | Runs each wave's tasks one at a time, in graph order.                     | Debuggability, rate-limited providers, deterministic logs |
| `parallel`   | Runs each wave's independent tasks concurrently (thread pool).            | I/O-bound provider calls, independent subtasks            |
| `supervisor` | Same as sequential/parallel, plus a designated agent synthesizes results. | Multi-perspective tasks that need one final answer         |

All three strategies share the same task-execution path
(`Orchestrator._run_task`), so adding a fourth strategy means adding a new
"wave runner" function, not touching task execution or result handling.

## Why a mock provider is a first-class citizen

Frameworks that only work against a live API are hard to test, hard to CI,
and hard for a contributor to try out without first acquiring credentials.
`MockProvider` accepts a `responses` dict of substring → canned reply, so an
example workflow's output is both deterministic and readable — the README's
"research team" example produces the same market-trends synthesis on every
run, on every machine, with zero setup.

## Extension points

- **New provider**: subclass `Provider`, implement `complete()`. Register it
  in `agentmesh/config.py::_build_provider` if you want YAML support.
- **New tool**: subclass `Tool`, implement `run(**kwargs) -> str`, register it
  on a `ToolRegistry` and attach that registry to an `Agent`.
- **New strategy**: add a value to the `Strategy` enum and a `run_wave_*`
  function in `orchestration/strategies.py`, then branch on it in
  `Orchestrator.run`.
