from agentmesh.config import load_workflow
from agentmesh.orchestration.strategies import Strategy

WORKFLOW = {
    "strategy": "sequential",
    "provider": {"type": "mock", "default": "ack"},
    "agents": [
        {"name": "writer", "system_prompt": "You write things."},
    ],
    "tasks": [
        {"id": "draft", "agent": "writer", "prompt": "Write a haiku about orchestration."},
    ],
}


def test_load_workflow_from_dict_builds_orchestrator_and_graph():
    orchestrator, graph = load_workflow(WORKFLOW)

    assert orchestrator.strategy == Strategy.SEQUENTIAL
    assert "writer" in orchestrator.agents
    assert "draft" in graph.tasks


def test_loaded_workflow_runs_end_to_end():
    orchestrator, graph = load_workflow(WORKFLOW)
    state = orchestrator.run(graph)

    assert state.results["draft"].output == "ack"
