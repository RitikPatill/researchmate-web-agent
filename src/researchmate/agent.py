from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AgentCallback(Protocol):
    """Structural protocol for UI callbacks during the agent loop."""

    def on_step(self, step: int, tool_name: str, tool_input: dict) -> None: ...  # noqa: D102

    def on_tool_result(
        self, step: int, tool_name: str, result_snippet: str, elapsed_s: float
    ) -> None: ...  # noqa: D102

    def on_complete(self, report_path: str) -> None: ...  # noqa: D102

    def on_error(self, message: str) -> None: ...  # noqa: D102


def run(
    question: str,
    *,
    max_steps: int = 10,
    model: str = "claude-sonnet-4-6",
    output_dir: str = "reports",
    callback: AgentCallback | None = None,
) -> str:
    """Run the research agent loop.

    Returns the absolute path to the saved report.
    Raises NotImplementedError until M2–M4 are wired up.
    """
    raise NotImplementedError("Agent loop not yet implemented (M2–M4)")
