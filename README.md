# AgentMesh

[![CI](https://github.com/codesanthan/agentmesh/actions/workflows/ci.yml/badge.svg)](https://github.com/codesanthan/agentmesh/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

A lightweight framework for orchestrating multi-agent AI systems: define a team
of agents, wire them into a dependency graph, and run that graph sequentially,
in parallel, or under a supervisor agent that synthesizes the team's output.

AgentMesh is deliberately small. It has one runtime dependency (`pyyaml`), no
vendor lock-in, and a mock LLM provider so the entire test suite, CI pipeline,
and example workflows run deterministically on any machine with no API keys.

## Why this exists

Most "multi-agent" demos are a single script calling an LLM in a loop. AgentMesh
instead treats a multi-agent system the way you'd treat any distributed
workload: as a **task graph** with explicit dependencies, a small number of
composable **execution strategies**, and a **provider boundary** that keeps the
orchestration logic independent of any one model vendor. That separation is
what makes the system testable, portable across machines, and easy to reason
about as it grows.

## How it works

```mermaid
flowchart LR
    subgraph Workflow definition
        Y[workflow.yaml]
    end

    Y -->|load_workflow| C[Config loader]
    C --> A1[Agent: researcher]
    C --> A2[Agent: analyst]
    C --> A3[Agent: lead]
    C --> G[TaskGraph]

    subgraph Orchestrator
        G --> W1[Wave 1: independent tasks]
        W1 --> W2[Wave 2: dependent tasks]
        W2 --> S[Supervisor synthesis]
    end

    A1 -.provider.complete.-> P[("LLM Provider:<br/>mock / anthropic / openai")]
    A2 -.provider.complete.-> P
    A3 -.provider.complete.-> P

    S --> R["ExecutionState<br/>(results + memory)"]
```

1. **Agents** (`agentmesh.core.Agent`) pair a system prompt with an LLM
   provider and keep their own conversation history.
2. **Tasks** are wired into a **TaskGraph** with `depends_on` edges. The graph
   validates itself (no missing dependencies, no cycles) and computes waves of
   tasks that can run concurrently.
3. The **Orchestrator** walks those waves under one of three strategies:
   - `sequential` — one task at a time, in dependency order.
   - `parallel` — each wave's independent tasks run concurrently via a thread pool.
   - `supervisor` — like sequential, plus a designated agent synthesizes every
     result into one final answer at the end.
4. Every task's result (including failures) is recorded in an
   **ExecutionState**, so a failed task never crashes the run — it's visible
   in the results and can be handled explicitly.
5. **Providers** are a thin interface (`complete(messages) -> str`). Ship with
   `MockProvider` (deterministic, no API key), `AnthropicProvider`, and
   `OpenAIProvider`. Swapping providers never touches orchestration code.

## Quickstart

```bash
git clone https://github.com/codesanthan/agentmesh.git
cd agentmesh
pip install -e ".[dev]"

# Run the example workflows (no API key required — uses the mock provider)
agentmesh run examples/research_team/workflow.yaml
agentmesh run examples/customer_support/workflow.yaml

# Run the test suite
make check
```

### Define a workflow

```yaml
# workflow.yaml
strategy: supervisor
supervisor: lead

provider:
  type: anthropic          # or "openai" / "mock"
  model: claude-sonnet-4-5

agents:
  - name: researcher
    system_prompt: You are a meticulous market researcher.
  - name: analyst
    system_prompt: You turn research into investment implications.
  - name: lead
    system_prompt: You synthesize your team's findings into one recommendation.

tasks:
  - id: research
    agent: researcher
    prompt: Summarize current market trends in enterprise AI adoption.
  - id: analysis
    agent: analyst
    depends_on: [research]
    prompt: Analyze the research findings for investment implications.
```

```bash
export ANTHROPIC_API_KEY=sk-...
agentmesh run workflow.yaml
```

### Or build it in Python directly

```python
from agentmesh import Agent, Orchestrator, Task, TaskGraph
from agentmesh.providers.mock_provider import MockProvider

provider = MockProvider(default="Acknowledged.")
agents = {"writer": Agent(name="writer", provider=provider)}

graph = TaskGraph()
graph.add(Task(id="draft", agent="writer", prompt="Write a haiku about orchestration."))

orchestrator = Orchestrator(agents=agents)
state = orchestrator.run(graph)
print(state.results["draft"].output)
```

## Project layout

```
src/agentmesh/
  core/            Agent, Message, Task, ExecutionState
  orchestration/   TaskGraph, execution strategies, Orchestrator
  providers/       Provider interface + mock/Anthropic/OpenAI backends
  tools/           Tool interface, registry, builtin tools
  config.py        YAML workflow loader
  cli.py           `agentmesh run <workflow.yaml>`
examples/          Runnable end-to-end workflows (mock provider, no API key)
tests/             pytest suite covering every module above
```

See [docs/architecture.md](docs/architecture.md) for a deeper look at the
design decisions and trade-offs.

## Reproducible builds

- Pinned, minimal dependencies (`pyyaml` at runtime; `pytest`/`ruff` for dev).
- `make setup`, `make test`, `make lint`, `make check` — the same four
  commands work identically on any machine.
- CI (`.github/workflows/ci.yml`) runs the full test suite and both example
  workflows on **Ubuntu, macOS, and Windows**, across **Python 3.10–3.12** —
  9 combinations on every push, so "works on my machine" isn't a question.

## Roadmap

- Async provider support for higher-throughput parallel waves.
- Streaming output from providers.
- A retry/backoff policy per task.
- Persistent execution state (resume a partially-failed run).

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
