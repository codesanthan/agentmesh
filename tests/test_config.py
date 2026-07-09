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


def test_agent_level_provider_overrides_workflow_default():
    workflow = {
        "strategy": "sequential",
        "provider": {"type": "mock", "default": "default-response"},
        "agents": [
            {"name": "writer", "system_prompt": "You write things."},
            {
                "name": "specialist",
                "system_prompt": "You are a specialist.",
                "provider": {"type": "mock", "default": "specialist-response"},
            },
        ],
        "tasks": [
            {"id": "draft", "agent": "writer", "prompt": "Write a haiku."},
            {"id": "specialist_task", "agent": "specialist", "prompt": "Say something."},
        ],
    }

    orchestrator, graph = load_workflow(workflow)
    state = orchestrator.run(graph)

    assert state.results["draft"].output == "default-response"
    assert state.results["specialist_task"].output == "specialist-response"
