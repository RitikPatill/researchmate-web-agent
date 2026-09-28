from __future__ import annotations

import typer

from researchmate import __version__

app = typer.Typer(help="ResearchMate — autonomous research agent powered by Claude.")


@app.command()
def main(
    question: str = typer.Argument(..., help="Research question to investigate."),
    max_steps: int = typer.Option(10, "--max-steps", help="Max tool-call iterations."),
    model: str = typer.Option("claude-sonnet-4-6", "--model", help="Claude model ID."),
    output_dir: str = typer.Option("reports", "--output-dir", help="Directory for saved reports."),
) -> None:
    print(f"ResearchMate v{__version__} — coming soon")
    raise typer.Exit()
