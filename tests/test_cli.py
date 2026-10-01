from __future__ import annotations

from typer.testing import CliRunner

from researchmate.cli import app

runner = CliRunner()


def test_dry_run_exits_zero() -> None:
    result = runner.invoke(app, ["What is a vector database?", "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output.lower()


def test_dry_run_shows_config() -> None:
    result = runner.invoke(
        app,
        ["test question", "--dry-run", "--max-steps", "5", "--model", "claude-haiku-4-5-20251001"],
    )
    assert result.exit_code == 0
    assert "claude-haiku-4-5-20251001" in result.output
    assert "5" in result.output


def test_missing_question_shows_error() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code != 0


def test_not_implemented_exits_cleanly() -> None:
    """Running without --dry-run hits NotImplementedError and exits 0 with advisory."""
    result = runner.invoke(app, ["some research question"])
    assert result.exit_code == 0
    assert "scaffold" in result.output.lower() or "not yet implemented" in result.output.lower()
