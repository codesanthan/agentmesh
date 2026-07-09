from pathlib import Path

import pytest

from agentmesh.config import load_workflow
from agentmesh.core.task import TaskStatus

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
EXAMPLE_WORKFLOWS = sorted(EXAMPLES_DIR.glob("*/workflow.yaml"))


@pytest.mark.parametrize("workflow_path", EXAMPLE_WORKFLOWS, ids=lambda p: p.parent.name)
def test_example_workflow_runs_without_error(workflow_path):
    orchestrator, graph = load_workflow(workflow_path)
    state = orchestrator.run(graph)

    assert state.results
    assert all(result.status == TaskStatus.SUCCEEDED for result in state.results.values())
