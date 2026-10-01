from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

_TOOL_COLOURS: dict[str, str] = {
    "web_search": "green",
    "fetch_page": "blue",
    "extract_sections": "yellow",
}
_DEFAULT_COLOUR = "white"
_SNIPPET_LEN = 80
_MAX_TABLE_ROWS = 12


@dataclass
class ToolEvent:
    step: int
    tool_name: str
    input_snippet: str
    result_snippet: str
    elapsed_s: float

    def __post_init__(self) -> None:
        # Truncate at construction so callers can rely on the guarantee.
        if len(self.input_snippet) > _SNIPPET_LEN:
            self.input_snippet = self.input_snippet[:_SNIPPET_LEN]
        if len(self.result_snippet) > _SNIPPET_LEN:
            self.result_snippet = self.result_snippet[:_SNIPPET_LEN]


class ResearchUI:
    """Rich Live display that also satisfies the AgentCallback protocol."""

    def __init__(
        self,
        question: str,
        max_steps: int,
        *,
        console: Console | None = None,
    ) -> None:
        self._question = question
        self._max_steps = max_steps
        self._console = console or Console()
        self._events: list[ToolEvent] = []
        self._current_step = 0
        self._current_tool = ""
        self._live: Live | None = None

    # ------------------------------------------------------------------
    # Context manager — wraps the Live session
    # ------------------------------------------------------------------

    def __enter__(self) -> "ResearchUI":
        self._live = Live(
            self._build_layout(),
            console=self._console,
            refresh_per_second=8,
            transient=False,
        )
        self._live.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        if self._live is not None:
            self._live.__exit__(None, None, None)
            self._live = None

    # ------------------------------------------------------------------
    # AgentCallback methods
    # ------------------------------------------------------------------

    def on_step(self, step: int, tool_name: str, tool_input: dict[str, Any]) -> None:
        self._current_step = step
        self._current_tool = tool_name
        # Store a pending event (result_snippet filled by on_tool_result)
        snippet = repr(tool_input)[:_SNIPPET_LEN]
        self._events.append(
            ToolEvent(
                step=step,
                tool_name=tool_name,
                input_snippet=snippet,
                result_snippet="…",
                elapsed_s=0.0,
            )
        )
        self._refresh()

    def on_tool_result(
        self, step: int, tool_name: str, result_snippet: str, elapsed_s: float
    ) -> None:
        snippet = result_snippet[:_SNIPPET_LEN]
        # Update the last matching pending event
        for ev in reversed(self._events):
            if ev.step == step and ev.tool_name == tool_name:
                ev.result_snippet = snippet
                ev.elapsed_s = elapsed_s
                break
        self._refresh()

    def on_complete(self, report_path: str) -> None:
        # Called OUTSIDE the Live context so output lands in normal terminal buffer.
        path = Path(report_path)
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            preview = "\n".join(lines[:30])
        else:
            preview = f"*(report not found at {report_path})*"
        self._console.print(
            Panel(Markdown(preview), title="[bold green]Report preview[/]", expand=False)
        )

    def on_error(self, message: str) -> None:
        # Also called OUTSIDE Live so it renders cleanly.
        self._console.print(f"[bold red]Error:[/] {message}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._build_layout())

    def _build_layout(self) -> Panel:
        """Compose the full display as a single Panel wrapping stacked renderables."""
        spinner_text = Text()
        spinner_text.append(f"Step {self._current_step}/{self._max_steps} — ")
        colour = _TOOL_COLOURS.get(self._current_tool, _DEFAULT_COLOUR)
        spinner_text.append(self._current_tool or "starting…", style=colour)

        spinner = Spinner("dots", text=spinner_text)
        header = Panel(spinner, title=f"[bold]ResearchMate[/] — {self._question[:60]}")

        table = self._build_table()

        # Stack header + table inside a plain panel
        from rich.console import Group  # type: ignore[attr-defined]

        return Panel(Group(header, table), border_style="dim")

    def _build_table(self) -> Table:
        table = Table(
            "Step", "Tool", "Input", "Output", "Time(s)",
            expand=True,
            show_lines=False,
            header_style="bold cyan",
        )
        for ev in self._events[-_MAX_TABLE_ROWS:]:
            colour = _TOOL_COLOURS.get(ev.tool_name, _DEFAULT_COLOUR)
            table.add_row(
                str(ev.step),
                Text(ev.tool_name, style=colour),
                ev.input_snippet,
                ev.result_snippet,
                f"{ev.elapsed_s:.2f}",
            )
        return table
