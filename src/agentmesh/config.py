"""Load an Orchestrator + TaskGraph from a workflow YAML/dict definition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agentmesh.core.agent import Agent
from agentmesh.core.task import Task
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
            )
        )
    if not graph.tasks:
        raise ConfigError("Workflow must define at least one task")

    strategy = Strategy(spec.get("strategy", "sequential"))
    orchestrator = Orchestrator(agents=agents, strategy=strategy, supervisor=spec.get("supervisor"))

    return orchestrator, graph
