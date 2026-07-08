# Contributing

Thanks for considering a contribution to AgentMesh.

## Setup

```bash
git clone https://github.com/codesanthan/agentmesh.git
cd agentmesh
make setup
```

## Before opening a PR

```bash
make check   # ruff lint + full pytest suite
```

All new behavior should ship with tests. The test suite runs entirely against
`MockProvider`, so no API keys are needed to contribute.

## Style

- Formatted and linted with [ruff](https://docs.astral.sh/ruff/) (`make lint` / `make format`).
- Type hints throughout; keep new public functions annotated.
- Prefer small, composable modules over large ones — see `docs/architecture.md`
  for the extension points new code should plug into.

## Reporting issues

Please open a GitHub issue with a minimal repro (a workflow YAML or a short
Python snippet) whenever possible.
