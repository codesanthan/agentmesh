"""Command-line entry point: `agentmesh run <workflow.yaml>`."""

from __future__ import annotations

import argparse
import sys

from agentmesh.config import load_workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentmesh", description="Run a multi-agent workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a workflow defined in a YAML file")
    run_parser.add_argument("workflow", help="Path to a workflow YAML file")
    run_parser.add_argument("--quiet", action="store_true", help="Only print the final result")

    args = parser.parse_args(argv)

    if args.command == "run":
        orchestrator, graph = load_workflow(args.workflow)
        state = orchestrator.run(graph)

        if not args.quiet:
            for task_id, result in state.results.items():
                print(f"--- {task_id} ({result.agent}) [{result.status.value}] ---")
                print(result.output or result.error or "")
                print()
        else:
            last = list(state.results.values())[-1]
            print(last.output)

        failures = [r for r in state.results.values() if r.status.value == "failed"]
        return 1 if failures else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
