from __future__ import annotations

import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from researchmate import __version__
from researchmate import agent
from researchmate.ui import ResearchUI

load_dotenv()  # resolve .env before typer evaluates Option defaults

app = typer.Typer(help="ResearchMate — autonomous research agent powered by Claude.")
console = Console()


def _print_dry_run(question: str, max_steps: int, model: str, output_dir: str) -> None:
    table = Table("Parameter", "Value", show_header=True, header_style="bold cyan")
    table.add_row("Question", question)
    table.add_row("Model", model)
    table.add_row("Max steps", str(max_steps))
    table.add_row("Output dir", str(Path(output_dir).resolve()))
    console.print(table)
    console.print("[yellow]\\[dry-run] No API call made.[/]")


@app.command()
def main(
    question: str = typer.Argument(..., help="Research question to investigate."),
    max_steps: int = typer.Option(
        int(os.getenv("MAX_STEPS", "10")), "--max-steps", help="Max tool-call iterations."
    ),
    model: str = typer.Option(
        os.getenv("MODEL", "claude-sonnet-4-6"), "--model", help="Claude model ID."
    ),
    output_dir: str = typer.Option(
        "reports", "--output-dir", help="Directory for saved reports."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run/--no-dry-run", help="Print config and plan; skip API call."
    ),
) -> None:
    if dry_run:
        _print_dry_run(question, max_steps, model, output_dir)
        raise typer.Exit()

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    ui = ResearchUI(question=question, max_steps=max_steps)
    try:
        with ui:
            report_path = agent.run(
                question,
                max_steps=max_steps,
                model=model,
                output_dir=output_dir,
                callback=ui,
            )
        ui.on_complete(report_path)
    except NotImplementedError:
        console.print("[yellow]Agent not yet implemented — scaffold only.[/]")
    except Exception as exc:  # noqa: BLE001
        ui.on_error(str(exc))
        raise typer.Exit(code=1)
