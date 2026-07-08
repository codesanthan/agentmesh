import pytest

from agentmesh.core.agent import Agent
from agentmesh.core.task import Task, TaskStatus
from agentmesh.orchestration.graph import TaskGraph
from agentmesh.orchestration.orchestrator import Orchestrator, OrchestratorError
from agentmesh.orchestration.strategies import Strategy
from agentmesh.providers.mock_provider import MockProvider


def _agents(*names):
    provider = MockProvider(default="done")
    return {name: Agent(name=name, provider=provider) for name in names}


def test_sequential_run_all_succeed():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="a", prompt="do 1"))
    graph.add(Task(id="t2", agent="a", prompt="do 2", depends_on=["t1"]))

    orchestrator = Orchestrator(agents=_agents("a"), strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    assert state.results["t1"].status == TaskStatus.SUCCEEDED
    assert state.results["t2"].status == TaskStatus.SUCCEEDED


def test_task_with_unknown_agent_fails_without_raising():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="ghost", prompt="do 1"))

    orchestrator = Orchestrator(agents=_agents("a"), strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    assert state.results["t1"].status == TaskStatus.FAILED
    assert "ghost" in state.results["t1"].error


def test_parallel_run_covers_all_tasks():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="a", prompt="do 1"))
    graph.add(Task(id="t2", agent="a", prompt="do 2"))
    graph.add(Task(id="t3", agent="a", prompt="do 3"))

    orchestrator = Orchestrator(agents=_agents("a"), strategy=Strategy.PARALLEL)
    state = orchestrator.run(graph)

    assert len(state.results) == 3
    assert all(r.status == TaskStatus.SUCCEEDED for r in state.results.values())


def test_supervisor_strategy_adds_synthesis_result():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="a", prompt="do 1"))
    graph.add(Task(id="t2", agent="a", prompt="do 2"))

    orchestrator = Orchestrator(
        agents=_agents("a", "lead"), strategy=Strategy.SUPERVISOR, supervisor="lead"
    )
    state = orchestrator.run(graph)

    assert "__supervisor_synthesis__" in state.results
    assert state.results["__supervisor_synthesis__"].agent == "lead"


def test_supervisor_strategy_without_supervisor_name_raises():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="a", prompt="do 1"))

    orchestrator = Orchestrator(agents=_agents("a"), strategy=Strategy.SUPERVISOR)

    with pytest.raises(OrchestratorError):
        orchestrator.run(graph)
