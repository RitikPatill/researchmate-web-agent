from __future__ import annotations

import json
import re
import time
from datetime import date
from typing import Protocol, runtime_checkable

import anthropic

from researchmate.report import Finding, ResearchReport, save_report
from researchmate.tools import (
    ExtractSectionsInput,
    FetchPageInput,
    WebSearchInput,
    extract_sections,
    fetch_page,
    web_search,
)


@runtime_checkable
class AgentCallback(Protocol):
    """Structural protocol for UI callbacks during the agent loop."""

    def on_step(self, step: int, tool_name: str, tool_input: dict) -> None: ...  # noqa: D102

    def on_tool_result(
        self, step: int, tool_name: str, result_snippet: str, elapsed_s: float
    ) -> None: ...  # noqa: D102

    def on_complete(self, report_path: str) -> None: ...  # noqa: D102

    def on_error(self, message: str) -> None: ...  # noqa: D102


_TOOLS: list[dict] = [
    {
        "name": "web_search",
        "description": "Search the web using DuckDuckGo. Returns up to 10 results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "Fetch a web page and return its title and visible text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch (must start with http:// or https://).",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "extract_sections",
        "description": "Split text into sections at paragraph boundaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to split into sections."},
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum chars per section (default 4000).",
                },
            },
            "required": ["text"],
        },
    },
]

_SYSTEM = (
    "You are ResearchMate, an autonomous research agent. "
    "Use the provided tools to investigate the user's question thoroughly. "
    "Search the web, fetch relevant pages, and extract key information. "
    "When you have gathered enough evidence, synthesise your findings into a JSON object "
    "with exactly these fields:\n"
    '{"summary": "...", "findings": [{"source_url": "...", "title": "...", '
    '"key_points": ["...", "..."], "confidence": "high|medium|low"}, ...]}\n'
    "Return ONLY the JSON object when done — no markdown fences, no additional text."
)


def _dispatch(tool_name: str, tool_input: dict) -> str:
    """Call the matching Python handler and return a JSON string result."""
    if tool_name == "web_search":
        return web_search(WebSearchInput(**tool_input)).model_dump_json()
    if tool_name == "fetch_page":
        return fetch_page(FetchPageInput(**tool_input)).model_dump_json()
    if tool_name == "extract_sections":
        return extract_sections(ExtractSectionsInput(**tool_input)).model_dump_json()
    raise ValueError(f"Unknown tool: {tool_name}")


def _parse_report_json(text: str) -> dict:
    """Extract and parse a JSON object from Claude's final text response."""
    text = text.strip()
    # Strip optional markdown code fences
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


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
    """
    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": question}]
    total_tokens = 0
    step = 0
    final_text = "{}"

    while step < max_steps:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=_SYSTEM,
            tools=_TOOLS,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )
        total_tokens += response.usage.input_tokens + response.usage.output_tokens

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # Claude finished — extract the JSON synthesis from the text block
            text_blocks = [b for b in response.content if b.type == "text"]
            final_text = text_blocks[0].text if text_blocks else "{}"
            break

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # Execute each tool call and collect results
        tool_results = []
        for tool_use in tool_uses:
            step += 1
            if callback is not None:
                callback.on_step(step, tool_use.name, tool_use.input)  # type: ignore[arg-type]

            t0 = time.perf_counter()
            try:
                result_json = _dispatch(tool_use.name, tool_use.input)  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001
                result_json = json.dumps({"error": str(exc)})
            elapsed = time.perf_counter() - t0

            if callback is not None:
                callback.on_tool_result(step, tool_use.name, result_json[:80], elapsed)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result_json,
                }
            )

            if step >= max_steps:
                break

        messages.append({"role": "user", "content": tool_results})

        if step >= max_steps:
            # Ask Claude to synthesise with whatever evidence it has collected so far
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "You have reached the maximum number of tool calls. "
                        "Synthesise your findings now and return the JSON report."
                    ),
                }
            )
            final_response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=_SYSTEM,
                messages=messages,  # type: ignore[arg-type]
            )
            total_tokens += (
                final_response.usage.input_tokens + final_response.usage.output_tokens
            )
            text_blocks = [b for b in final_response.content if b.type == "text"]
            final_text = text_blocks[0].text if text_blocks else "{}"
            break

    data = _parse_report_json(final_text)
    report = ResearchReport(
        question=question,
        summary=data.get("summary", "No summary available."),
        findings=[Finding(**f) for f in data.get("findings", [])],
        model=model,
        date=date.today().isoformat(),
        total_tokens=total_tokens,
    )
    path = save_report(report, output_dir)
    return path
