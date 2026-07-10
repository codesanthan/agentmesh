import pytest

from agentmesh.core.agent import Agent
from agentmesh.core.state import ExecutionState
from agentmesh.core.task import Task, TaskResult, TaskStatus
from agentmesh.core.usage import Usage
from agentmesh.orchestration.graph import TaskGraph
from agentmesh.orchestration.orchestrator import Orchestrator
from agentmesh.orchestration.strategies import Strategy
from agentmesh.providers.mock_provider import MockProvider


def test_usage_addition_sums_fields():
    a = Usage(input_tokens=10, output_tokens=5, cost_usd=0.01)
    b = Usage(input_tokens=3, output_tokens=7, cost_usd=0.02)

    total = a + b

    assert total.input_tokens == 13
    assert total.output_tokens == 12
    assert total.cost_usd == pytest.approx(0.03)
    assert total.total_tokens == 25


def test_mock_provider_reports_free_but_nonzero_token_usage():
    agent = Agent(name="writer", provider=MockProvider(default="a short reply here"))

    output, usage = agent.act_with_usage("Write something.")

    assert output == "a short reply here"
    assert usage.cost_usd == 0.0
    assert usage.input_tokens > 0
    assert usage.output_tokens == 4


def test_orchestrator_attaches_usage_to_successful_results():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="writer", prompt="Write a haiku."))

    provider = MockProvider(default="line one line two line three")
    agents = {"writer": Agent(name="writer", provider=provider)}
    orchestrator = Orchestrator(agents=agents, strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    result = state.results["t1"]
    assert result.usage is not None
    assert result.usage.output_tokens == 5


def test_orchestrator_leaves_usage_none_on_failure():
    graph = TaskGraph()
    graph.add(Task(id="t1", agent="ghost", prompt="do 1"))

    agents = {"writer": Agent(name="writer", provider=MockProvider(default="x"))}
    orchestrator = Orchestrator(agents=agents, strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    assert state.results["t1"].usage is None


def test_execution_state_totals_and_per_agent_usage():
    state = ExecutionState()
    state.record(
        TaskResult(task_id="t1", agent="a", status=TaskStatus.SUCCEEDED, usage=Usage(1, 2, 0.0))
    )
    state.record(
        TaskResult(task_id="t2", agent="a", status=TaskStatus.SUCCEEDED, usage=Usage(3, 4, 0.0))
    )
    state.record(
        TaskResult(task_id="t3", agent="b", status=TaskStatus.SUCCEEDED, usage=Usage(5, 6, 0.01))
    )
    state.record(TaskResult(task_id="t4", agent="c", status=TaskStatus.FAILED))

    total = state.total_usage()
    by_agent = state.usage_by_agent()

    assert total.input_tokens == 9
    assert total.output_tokens == 12
    assert total.cost_usd == pytest.approx(0.01)
    assert by_agent["a"].input_tokens == 4
    assert by_agent["b"].output_tokens == 6
    assert "c" not in by_agent
