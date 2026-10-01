from __future__ import annotations

import io

from rich.console import Console

from researchmate.ui import ResearchUI, ToolEvent, _SNIPPET_LEN


def _silent_console() -> Console:
    return Console(file=io.StringIO(), force_terminal=False)


def test_tool_event_snippet_truncation() -> None:
    ev = ToolEvent(
        step=1,
        tool_name="web_search",
        input_snippet="x" * 200,
        result_snippet="y" * 200,
        elapsed_s=0.5,
    )
    assert len(ev.input_snippet) <= _SNIPPET_LEN
    assert len(ev.result_snippet) <= _SNIPPET_LEN


def test_tool_event_short_snippets_unchanged() -> None:
    ev = ToolEvent(
        step=1,
        tool_name="fetch_page",
        input_snippet="short",
        result_snippet="also short",
        elapsed_s=1.0,
    )
    assert ev.input_snippet == "short"
    assert ev.result_snippet == "also short"


def test_research_ui_accumulates_events() -> None:
    ui = ResearchUI("test question", max_steps=5, console=_silent_console())
    ui.on_step(1, "web_search", {"query": "test"})
    ui.on_tool_result(1, "web_search", "some result", 0.3)
    assert len(ui._events) == 1
    assert ui._events[0].result_snippet == "some result"
    assert ui._events[0].elapsed_s == 0.3


def test_research_ui_multiple_steps() -> None:
    ui = ResearchUI("multi step question", max_steps=10, console=_silent_console())
    for i in range(1, 4):
        ui.on_step(i, "web_search", {"query": f"query {i}"})
        ui.on_tool_result(i, "web_search", f"result {i}", float(i) * 0.1)
    assert len(ui._events) == 3
    assert ui._current_step == 3


def test_research_ui_caps_table_at_12_rows() -> None:
    ui = ResearchUI("big run", max_steps=20, console=_silent_console())
    for i in range(1, 16):
        ui.on_step(i, "fetch_page", {"url": f"http://example.com/{i}"})
        ui.on_tool_result(i, "fetch_page", f"content {i}", 0.1)
    # All events are stored; rendering slices the last 12
    assert len(ui._events) == 15
    table = ui._build_table()
    assert table.row_count == 12
