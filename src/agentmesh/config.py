"""Load an Orchestrator + TaskGraph from a workflow YAML/dict definition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agentmesh.core import validators as builtin_validators
from agentmesh.core.agent import Agent
from agentmesh.core.task import Task
from agentmesh.core.validators import Validator
from agentmesh.orchestration.graph import TaskGraph
from agentmesh.orchestration.orchestrator import Orchestrator
from agentmesh.orchestration.strategies import Strategy
from agentmesh.providers.base import Provider
from agentmesh.providers.mock_provider import MockProvider


class ConfigError(Exception):
    pass


def _build_provider(spec: dict[str, Any]) -> Provider:
    provider_type = spec.get("type", "mock")
    if provider_type == "mock":
        return MockProvider(responses=spec.get("responses"), default=spec.get("default"))
    if provider_type == "anthropic":
        from agentmesh.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=spec.get("model", "claude-sonnet-4-5"))
    if provider_type == "openai":
        from agentmesh.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(model=spec.get("model", "gpt-4o-mini"))
    raise ConfigError(f"Unknown provider type '{provider_type}'")


def _build_validator(spec: dict[str, Any] | list[Any] | None) -> Validator | None:
    """Build a `Task.validate` callable from a YAML `validate:` block.

    Supported types:
      - `non_empty` (args: `min_length`, default 1)
      - `not_contains` (args: `markers`, a list of substrings)
    Pass a list of specs to require all of them to pass.
    """
    if not spec:
        return None
    if isinstance(spec, list):
        checks = [_build_validator(item) for item in spec]
        return builtin_validators.all_of(*[c for c in checks if c is not None])

    validator_type = spec.get("type")
    if validator_type == "non_empty":
        return builtin_validators.non_empty(min_length=spec.get("min_length", 1))
    if validator_type == "not_contains":
        return builtin_validators.not_contains(*spec.get("markers", []))
    raise ConfigError(f"Unknown validator type '{validator_type}'")


def load_workflow(source: str | Path | dict[str, Any]) -> tuple[Orchestrator, TaskGraph]:
    """Build an (Orchestrator, TaskGraph) pair from a YAML file path or a dict."""
    if isinstance(source, dict):
        spec = source
    else:
        path = Path(source)
        spec = yaml.safe_load(path.read_text())

    default_provider = _build_provider(spec.get("provider", {"type": "mock"}))

    agents: dict[str, Agent] = {}
    for agent_spec in spec.get("agents", []):
        agent_provider = (
            _build_provider(agent_spec["provider"])
            if "provider" in agent_spec
            else default_provider
        )
        agents[agent_spec["name"]] = Agent(
            name=agent_spec["name"],
            provider=agent_provider,
            system_prompt=agent_spec.get("system_prompt", "You are a helpful assistant."),
        )
    if not agents:
        raise ConfigError("Workflow must define at least one agent")

    graph = TaskGraph()
    for task_spec in spec.get("tasks", []):
        graph.add(
            Task(
                id=task_spec["id"],
                agent=task_spec["agent"],
                prompt=task_spec["prompt"],
                depends_on=task_spec.get("depends_on", []),
                max_retries=task_spec.get("max_retries", 0),
                validate=_build_validator(task_spec.get("validate")),
            )
        )
    if not graph.tasks:
        raise ConfigError("Workflow must define at least one task")

    strategy = Strategy(spec.get("strategy", "sequential"))
    orchestrator = Orchestrator(agents=agents, strategy=strategy, supervisor=spec.get("supervisor"))

    return orchestrator, graph
