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

This extends to two failure modes that are easy to miss if you only think in
terms of exceptions:

- **A task can retry itself with its own failure as context.** Set
  `Task.max_retries`, and `Orchestrator._run_task` will re-invoke the same
  task, appending a `[Retry N feedback: ...]` block describing what went
  wrong to the context passed into the next attempt -- whether that failure
  was an exception or a validator rejection. The agent sees its own mistake
  instead of blindly repeating it. Usage/cost across all attempts is summed
  into the final `TaskResult`.
- **"Succeeded" isn't the same as "good."** A provider call can return
  cleanly with output that's empty, truncated, or a refusal -- nothing
  raises, so a bare try/except can never catch it. `Task.validate` (see
  `core/validators.py`) is a `Callable[[str], str | None]` that inspects the
  output after the call returns and can reject it with a reason, feeding
  that reason back into the retry loop the same way an exception would.

**A failed dependency never silently becomes blank context.** Before running
a task, the orchestrator checks that every task in `depends_on` reached
`TaskStatus.SUCCEEDED`; if any didn't, the task is recorded as `SKIPPED`
(with an error naming the dependency) instead of running on a corrupted
picture of its inputs. `ExecutionState.context_for()` also only includes
successful upstream results as defense in depth, so a failed or skipped
dependency never gets stitched into a downstream agent's prompt as if
nothing were wrong.

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
"wave runner" function, not touching task execution, retry, or result
handling.

## Why a mock provider is a first-class citizen

Frameworks that only work against a live API are hard to test, hard to CI,
and hard for a contributor to try out without first acquiring credentials.
`MockProvider` accepts a `responses` dict of substring → canned reply, so an
example workflow's output is both deterministic and readable — the README's
"research team" example produces the same market-trends synthesis on every
run, on every machine, with zero setup. This also makes retry behavior
itself testable without a live model: `tests/test_retry.py` proves a task
recovers by changing what `MockProvider` matches once retry feedback lands
in the context, the same way a real model would react to seeing its own
mistake.

## Extension points

- **New provider**: subclass `Provider`, implement `complete()`. Register it
  in `agentmesh/config.py::_build_provider` if you want YAML support.
- **New validator**: write a `Callable[[str], str | None]` (or compose
  existing ones with `core.validators.all_of`), attach it to `Task.validate`.
  Register a `type` name in `agentmesh/config.py::_build_validator` if you
  want it configurable from workflow YAML.
- **New tool**: subclass `Tool`, implement `run(**kwargs) -> str`, register it
  on a `ToolRegistry` and attach that registry to an `Agent`.
- **New strategy**: add a value to the `Strategy` enum and a `run_wave_*`
  function in `orchestration/strategies.py`, then branch on it in
  `Orchestrator.run`.
