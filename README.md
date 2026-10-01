# ResearchMate — Autonomous Web Research Agent


> **Video walkthrough:** https://youtu.be/47lHOdThXqc
> **60-second overview:** https://youtu.be/dOg98Abqw4M

> A CLI agent that uses Claude tool-use to browse the web, synthesise sources, and emit structured Markdown research reports.

<!-- TODO: replace with a 5-10 second demo gif. Record with ScreenToGif on
     Windows or peek on macOS. Save to docs/demo.gif and update path here. -->
![demo](docs/demo.gif)

## What it is

ResearchMate is a terminal-first autonomous research agent. You hand it a question and it does the legwork: it breaks the question into sub-queries, iteratively calls its own tool set (web search, page fetcher, text extractor) until it has enough evidence, then emits a structured Markdown report with an executive summary, per-source findings, confidence notes, and a sources table.

The agent loop runs on `claude-sonnet-4-6` in tool-use mode. Claude decides when it has gathered sufficient evidence; a configurable `MAX_STEPS` guard caps the maximum number of tool calls so runaway queries never happen. No paid search API is required — web search is handled by scraping DuckDuckGo HTML directly.

## Quickstart

```bash
git clone https://github.com/RitikPatill/researchmate-web-agent.git
cd researchmate-web-agent

# Python 3.11+ required
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .

cp .env.example .env
# Open .env and set ANTHROPIC_API_KEY=sk-ant-...

researchmate "What are the best open-source vector databases in 2026?"
# Report saved to ./reports/what-are-the-best-open-source-vector-databases-i.md
```

## Usage

Run a research query with default settings (10 steps, `claude-sonnet-4-6`, output to `./reports/`):

```bash
researchmate "What are the best open-source vector databases in 2026?"
```

Resolve configuration and exit without making an API call:

```bash
researchmate "Explain RAG vs fine-tuning trade-offs" --dry-run
```

Override model, step limit, and output directory:

```bash
researchmate "Explain RAG vs fine-tuning trade-offs" \
    --max-steps 15 \
    --model claude-haiku-4-5-20251001 \
    --output-dir ./out
```

While running, `rich` renders an animated spinner showing the current step and tool name, a scrolling tool-call log table, and a Markdown report preview panel on completion. All flags can also be set via `.env` variables (`MAX_STEPS`, `MODEL`); CLI flags take precedence.

## Architecture

```
CLI (typer)
  │
  ├── ResearchUI (rich Live display)
  │     spinner · tool-call log · report preview
  │
  └── Agent Loop (claude-sonnet-4-6, tool-use)
        │
        ├── web_search      DuckDuckGo HTML scraper
        ├── fetch_page      httpx + BeautifulSoup
        └── extract_sections  text chunker
              │
              └── Report Writer
                    Pydantic schema → Markdown + YAML front-matter
                    saved to <output-dir>/<slug>.md
```

## Project structure

```
researchmate-web-agent/
├── src/researchmate/     # package source
│   ├── cli.py            # typer entry point; flags and .env resolution
│   ├── ui.py             # rich Live display (spinner, log table, preview)
│   ├── agent.py          # tool-use loop; AgentCallback protocol
│   ├── tools.py          # web_search / fetch_page / extract_sections + Pydantic schemas
│   └── report.py         # ResearchReport schema, to_markdown(), save_report()
├── tests/                # pytest suite (no network, no API key required)
├── docs/                 # demo.gif lives here (generated locally)
├── reports/              # generated reports, git-ignored
├── demo.tape             # VHS script to regenerate docs/demo.gif
├── .env.example          # ANTHROPIC_API_KEY, MAX_STEPS, MODEL
└── pyproject.toml        # hatchling build, pinned dependencies
```

## Roadmap

- [ ] Streaming output: surface Claude's partial text tokens in the live display as they arrive.
- [ ] Caching layer: persist fetched pages to disk to avoid redundant HTTP requests across runs.
- [ ] Plugin API: allow third-party tools to register alongside the built-in three without forking `agent.py`.
- [ ] HTML report export: render the Markdown report to a self-contained HTML file via `mistune`.
- [ ] Token-cost accounting: surface prompt/completion token counts and estimated USD cost in the report front-matter.

## License

MIT — see [LICENSE](LICENSE).

---

Built autonomously by [autodev](https://github.com/RitikPatill/autodev),
a multi-agent orchestrator I designed. Each commit in this repo was
authored by me; the implementation work was performed by Sonnet under
the orchestrator's control. Read the orchestrator's README to see how.
