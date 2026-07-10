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
    run_parser.add_argument(
        "--usage",
        action="store_true",
        help="Print a per-agent token/cost summary after the run",
    )

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

        if args.usage:
            print("--- usage ---")
            for agent_name, usage in state.usage_by_agent().items():
                print(
                    f"{agent_name}: {usage.input_tokens} in / {usage.output_tokens} out "
                    f"tokens, ${usage.cost_usd:.4f}"
                )
            total = state.total_usage()
            print(
                f"total: {total.input_tokens} in / {total.output_tokens} out tokens, "
                f"${total.cost_usd:.4f}"
            )

        failures = [r for r in state.results.values() if r.status.value == "failed"]
        return 1 if failures else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
