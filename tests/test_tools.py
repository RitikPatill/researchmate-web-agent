from __future__ import annotations

import pytest
from pydantic import ValidationError

from researchmate.report import Finding, ResearchReport, to_markdown
from researchmate.tools import (
    ExtractSectionsInput,
    FetchPageInput,
    WebSearchInput,
    extract_sections,
)


# ---------------------------------------------------------------------------
# Test 1 — tool schema validation
# ---------------------------------------------------------------------------

def test_tool_input_schemas_reject_invalid() -> None:
    with pytest.raises(ValidationError):
        WebSearchInput(query="")           # blank query

    with pytest.raises(ValidationError):
        WebSearchInput(query="   ")        # whitespace-only query

    with pytest.raises(ValidationError):
        FetchPageInput(url="not-a-url")    # no http scheme

    with pytest.raises(ValidationError):
        FetchPageInput(url="ftp://example.com")  # wrong scheme

    with pytest.raises(ValidationError):
        ExtractSectionsInput(text="x", max_chars=0)   # non-positive


# ---------------------------------------------------------------------------
# Test 2 — HTML extractor (pure unit, no HTTP)
# ---------------------------------------------------------------------------

def test_extract_sections_splits_on_paragraphs() -> None:
    para = "Alpha beta gamma.\n\nDelta epsilon.\n\nZeta eta."
    result = extract_sections(ExtractSectionsInput(text=para, max_chars=200))
    assert len(result.sections) >= 2
    assert all(s.strip() for s in result.sections)


def test_extract_sections_single_large_paragraph() -> None:
    """A single paragraph under max_chars returns one section."""
    text = "Only one paragraph here with no double newlines."
    result = extract_sections(ExtractSectionsInput(text=text, max_chars=200))
    assert len(result.sections) == 1
    assert result.sections[0] == text


def test_extract_sections_respects_max_chars() -> None:
    """Paragraphs are grouped until max_chars is exceeded, then a new section starts."""
    # 5 short paragraphs; max_chars forces a split before all 5 fit in one section
    parts = [f"Paragraph {i} content here." for i in range(5)]
    text = "\n\n".join(parts)
    result = extract_sections(ExtractSectionsInput(text=text, max_chars=50))
    assert len(result.sections) > 1


# ---------------------------------------------------------------------------
# Test 3 — report serialisation
# ---------------------------------------------------------------------------

def test_report_to_markdown_contains_front_matter_and_headings() -> None:
    report = ResearchReport(
        question="What is a vector database?",
        summary="A vector database stores embeddings.",
        findings=[
            Finding(
                source_url="https://example.com",
                title="VecDB",
                key_points=["fast ANN search"],
                confidence="high",
            )
        ],
        model="claude-sonnet-4-6",
        date="2026-10-01",
        total_tokens=1234,
    )
    md = to_markdown(report)
    assert md.startswith("---\n")
    assert "## Executive Summary" in md
    assert "## Findings" in md
    assert "## Sources" in md
    assert "vector database" in md.lower()
    assert "claude-sonnet-4-6" in md
    assert "2026-10-01" in md
    assert "1234" in md
