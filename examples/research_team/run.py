"""Run the research-team example using the Python API directly (no YAML)."""

from pathlib import Path

from agentmesh.config import load_workflow

WORKFLOW = Path(__file__).parent / "workflow.yaml"


def main() -> None:
    orchestrator, graph = load_workflow(WORKFLOW)
    state = orchestrator.run(graph)

    for task_id, result in state.results.items():
        print(f"--- {task_id} ({result.agent}) [{result.status.value}] ---")
        print(result.output)
        print()


if __name__ == "__main__":
    main()
