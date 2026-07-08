import pytest

from agentmesh.core.task import Task
from agentmesh.orchestration.graph import GraphError, TaskGraph


def _task(id_, depends_on=None):
    return Task(id=id_, prompt="p", agent="a", depends_on=depends_on or [])


def test_topological_order_respects_dependencies():
    graph = TaskGraph()
    graph.add(_task("a"))
    graph.add(_task("b", ["a"]))
    graph.add(_task("c", ["a"]))
    graph.add(_task("d", ["b", "c"]))

    waves = graph.topological_order()

    assert waves[0] == ["a"]
    assert set(waves[1]) == {"b", "c"}
    assert waves[2] == ["d"]


def test_validate_raises_on_unknown_dependency():
    graph = TaskGraph()
    graph.add(_task("a", ["missing"]))

    with pytest.raises(GraphError):
        graph.validate()


def test_validate_raises_on_cycle():
    graph = TaskGraph()
    graph.add(_task("a", ["b"]))
    graph.add(_task("b", ["a"]))

    with pytest.raises(GraphError):
        graph.validate()


def test_add_duplicate_task_raises():
    graph = TaskGraph()
    graph.add(_task("a"))

    with pytest.raises(GraphError):
        graph.add(_task("a"))
