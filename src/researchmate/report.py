from __future__ import annotations

import os
import re

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    source_url: str
    title: str
    key_points: list[str]
    confidence: str  # "high" | "medium" | "low"


class ResearchReport(BaseModel):
    question: str
    summary: str
    findings: list[Finding]
    model: str
    date: str          # ISO-8601
    total_tokens: int


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def to_markdown(report: ResearchReport) -> str:
    """Return YAML front-matter + Markdown body string."""
    fm = (
        "---\n"
        f'question: "{report.question}"\n'
        f"model: {report.model}\n"
        f"date: {report.date}\n"
        f"total_tokens: {report.total_tokens}\n"
        "---\n"
    )

    body_lines: list[str] = [
        f"# {report.question}",
        "",
        "## Executive Summary",
        "",
        report.summary,
        "",
        "## Findings",
        "",
    ]

    for i, f in enumerate(report.findings, 1):
        body_lines += [
            f"### {i}. {f.title}",
            "",
            f"**Confidence:** {f.confidence}  ",
            f"**Source:** <{f.source_url}>",
            "",
        ]
        for kp in f.key_points:
            body_lines.append(f"- {kp}")
        body_lines.append("")

    body_lines += [
        "## Sources",
        "",
        "| # | Title | URL |",
        "|---|---|---|",
    ]
    for i, f in enumerate(report.findings, 1):
        body_lines.append(f"| {i} | {f.title} | {f.source_url} |")

    return fm + "\n".join(body_lines) + "\n"


def save_report(report: ResearchReport, output_dir: str) -> str:
    """Slugify question → filename, write to output_dir/<slug>.md, return abs path."""
    slug = re.sub(r"[^a-z0-9]+", "-", report.question.lower()).strip("-")[:60]
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.abspath(os.path.join(output_dir, f"{slug}.md"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(to_markdown(report))
    return path
