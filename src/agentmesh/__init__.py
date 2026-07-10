"""AgentMesh: a lightweight framework for orchestrating multi-agent AI systems."""

from agentmesh.core.agent import Agent
from agentmesh.core.message import Message
from agentmesh.core.task import Task, TaskResult
from agentmesh.core.usage import Usage
from agentmesh.orchestration.graph import TaskGraph
from agentmesh.orchestration.orchestrator import Orchestrator

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Message",
    "Task",
    "TaskResult",
    "Usage",
    "Orchestrator",
    "TaskGraph",
    "__version__",
]
