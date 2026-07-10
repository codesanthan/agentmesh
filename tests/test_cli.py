from pathlib import Path

from agentmesh.cli import main

EXAMPLE = Path(__file__).parent.parent / "examples" / "research_team" / "workflow.yaml"


def test_cli_run_returns_zero_on_success(capsys):
    exit_code = main(["run", str(EXAMPLE)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "research" in captured.out


def test_cli_run_quiet_prints_only_final_output(capsys):
    exit_code = main(["run", str(EXAMPLE), "--quiet"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() != ""


def test_cli_run_with_usage_flag_prints_summary(capsys):
    exit_code = main(["run", str(EXAMPLE), "--usage"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "--- usage ---" in captured.out
    assert "total:" in captured.out
