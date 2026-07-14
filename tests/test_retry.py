from agentmesh.config import load_workflow
from agentmesh.core.agent import Agent
from agentmesh.core.message import Message
from agentmesh.core.state import ExecutionState
from agentmesh.core.task import Task, TaskResult, TaskStatus
from agentmesh.core.usage import Usage
from agentmesh.core.validators import all_of, non_empty, not_contains
from agentmesh.orchestration.graph import TaskGraph
from agentmesh.orchestration.orchestrator import Orchestrator
from agentmesh.orchestration.strategies import Strategy
from agentmesh.providers.base import Provider
from agentmesh.providers.mock_provider import MockProvider


class FlakyProvider(Provider):
    """Raises on the first `fail_times` calls, then succeeds.

    Used to exercise retry-on-exception without needing a real API -- the
    orchestrator's retry loop can't be tested with MockProvider alone since
    MockProvider never raises.
    """

    name = "flaky"

    def __init__(self, fail_times: int, reply: str = "steady output"):
        self.fail_times = fail_times
        self.reply = reply
        self.calls = 0

    def complete(self, messages: list[Message], **kwargs) -> str:
        return self.complete_with_usage(messages, **kwargs)[0]

    def complete_with_usage(self, messages: list[Message], **kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"transient failure #{self.calls}")
        return self.reply, Usage(input_tokens=1, output_tokens=1)


def test_task_retries_on_exception_then_succeeds():
    provider = FlakyProvider(fail_times=2)
    agent = Agent(name="worker", provider=provider)

    graph = TaskGraph()
    graph.add(Task(id="t1", agent="worker", prompt="do it", max_retries=2))

    orchestrator = Orchestrator(agents={"worker": agent}, strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    result = state.results["t1"]
    assert result.status == TaskStatus.SUCCEEDED
    assert result.output == "steady output"
    assert result.attempts == 3
    assert provider.calls == 3


def test_task_exhausts_retries_and_fails():
    provider = FlakyProvider(fail_times=5)
    agent = Agent(name="worker", provider=provider)

    graph = TaskGraph()
    graph.add(Task(id="t1", agent="worker", prompt="do it", max_retries=2))

    orchestrator = Orchestrator(agents={"worker": agent}, strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    result = state.results["t1"]
    assert result.status == TaskStatus.FAILED
    assert result.attempts == 3
    assert "transient failure #3" in result.error
    assert provider.calls == 3


def test_task_retries_on_validator_failure_with_feedback_in_context():
    # MockProvider is deterministic and substring-keyed: the first attempt's
    # prompt has no retry feedback in it, so it falls through to "garbage".
    # The retry loop appends "[Retry 1 feedback: ...]" to the context on the
    # second attempt, which changes what MockProvider matches against -- so
    # a good response is only reachable by the agent actually "seeing" the
    # failure reason, exactly like it would with a real model.
    provider = MockProvider(
        default="garbage",
        responses={"retry 1 feedback": "a properly detailed response"},
    )
    agent = Agent(name="writer", provider=provider)

    graph = TaskGraph()
    graph.add(
        Task(
            id="t1",
            agent="writer",
            prompt="write something",
            max_retries=1,
            validate=non_empty(min_length=10),
        )
    )

    orchestrator = Orchestrator(agents={"writer": agent}, strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    result = state.results["t1"]
    assert result.status == TaskStatus.SUCCEEDED
    assert result.output == "a properly detailed response"
    assert result.attempts == 2


def test_dependent_task_is_skipped_when_dependency_fails():
    provider = FlakyProvider(fail_times=1)
    agents = {
        "worker": Agent(name="worker", provider=provider),
        "follower": Agent(name="follower", provider=MockProvider(default="ok")),
    }

    graph = TaskGraph()
    graph.add(Task(id="t1", agent="worker", prompt="do it"))
    graph.add(Task(id="t2", agent="follower", prompt="build on t1", depends_on=["t1"]))

    orchestrator = Orchestrator(agents=agents, strategy=Strategy.SEQUENTIAL)
    state = orchestrator.run(graph)

    assert state.results["t1"].status == TaskStatus.FAILED
    t2 = state.results["t2"]
    assert t2.status == TaskStatus.SKIPPED
    assert "t1" in t2.error


def test_context_for_excludes_non_succeeded_dependencies():
    state = ExecutionState()
    state.record(
        TaskResult(task_id="ok", agent="a", status=TaskStatus.SUCCEEDED, output="good data")
    )
    state.record(TaskResult(task_id="bad", agent="a", status=TaskStatus.FAILED, error="boom"))

    context = state.context_for(["ok", "bad"])

    assert "[ok] good data" in context
    assert "bad" not in context


def test_validators_all_of_stops_at_first_failure():
    validator = all_of(non_empty(min_length=5), not_contains("banned"))

    assert validator("hi") is not None  # too short
    assert validator("this has a banned word") is not None
    assert validator("this is fine") is None


def test_workflow_config_supports_retry_and_validator():
    workflow = {
        "strategy": "sequential",
        "provider": {
            "type": "mock",
            "default": "x",
            "responses": {"retry 1 feedback": "a sufficiently long response"},
        },
        "agents": [{"name": "writer"}],
        "tasks": [
            {
                "id": "draft",
                "agent": "writer",
                "prompt": "write something",
                "max_retries": 1,
                "validate": {"type": "non_empty", "min_length": 10},
            }
        ],
    }

    orchestrator, graph = load_workflow(workflow)
    state = orchestrator.run(graph)

    result = state.results["draft"]
    assert result.status == TaskStatus.SUCCEEDED
    assert result.attempts == 2
    assert result.output == "a sufficiently long response"
