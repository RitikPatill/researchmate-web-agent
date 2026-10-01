from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchInput(BaseModel):
    query: str

    @field_validator("query", mode="before")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("query must not be blank")
        return value


class WebSearchResult(BaseModel):
    hits: list[SearchHit]


class FetchPageInput(BaseModel):
    url: str

    @field_validator("url", mode="before")
    @classmethod
    def url_must_have_http_scheme(cls, value: str) -> str:
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return value


class FetchPageResult(BaseModel):
    url: str
    title: str
    text: str


class ExtractSectionsInput(BaseModel):
    text: str
    max_chars: int = 4000

    @field_validator("max_chars", mode="before")
    @classmethod
    def max_chars_positive(cls, value: int) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("max_chars must be > 0")
        return value


class ExtractSectionsResult(BaseModel):
    sections: list[str]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def web_search(inp: WebSearchInput) -> WebSearchResult:
    """Search DuckDuckGo HTML endpoint and return up to 10 hits."""
    url = "https://html.duckduckgo.com/html/"
    resp = httpx.post(url, data={"q": inp.query}, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    hits: list[SearchHit] = []
    for result in soup.select(".result__body"):
        title_tag = result.select_one(".result__title")
        url_tag = result.select_one(".result__url")
        snippet_tag = result.select_one(".result__snippet")
        if not title_tag or not url_tag:
            continue
        hits.append(
            SearchHit(
                title=title_tag.get_text(strip=True),
                url=url_tag.get_text(strip=True),
                snippet=snippet_tag.get_text(strip=True) if snippet_tag else "",
            )
        )
        if len(hits) >= 10:
            break
    return WebSearchResult(hits=hits)


def fetch_page(inp: FetchPageInput) -> FetchPageResult:
    """Fetch a URL and return its title and visible text."""
    resp = httpx.get(inp.url, headers=_HEADERS, timeout=10, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else ""
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return FetchPageResult(url=str(resp.url), title=title, text=text)


def extract_sections(inp: ExtractSectionsInput) -> ExtractSectionsResult:
    """Split text on double newlines; each paragraph becomes its own section.

    Paragraphs longer than max_chars are further split at whitespace boundaries.
    """
    raw_chunks = [c.strip() for c in inp.text.split("\n\n")]
    raw_chunks = [c for c in raw_chunks if c]

    sections: list[str] = []
    for chunk in raw_chunks:
        if len(chunk) <= inp.max_chars:
            sections.append(chunk)
        else:
            # Hard-split long chunks at word boundaries
            start = 0
            while start < len(chunk):
                end = start + inp.max_chars
                if end >= len(chunk):
                    sections.append(chunk[start:])
                    break
                # Walk back to last space
                split_at = chunk.rfind(" ", start, end)
                if split_at <= start:
                    split_at = end
                sections.append(chunk[start:split_at].strip())
                start = split_at + 1

    return ExtractSectionsResult(sections=sections)
