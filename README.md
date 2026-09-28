# ResearchMate

A terminal-first autonomous research agent powered by Claude. Give it a question and it does the legwork: searches the web, reads pages, synthesises findings, and saves a structured Markdown report — no paid search API required.

## Status

| Milestone | Scope | State |
|---|---|---|
| **M1** | Repo scaffold: `src/` layout, pinned deps, CLI entry point stub, `.env.example`, MIT license | **done** |
| M2 | Agent loop: Claude tool-use, `web_search`, `fetch_page`, `extract_sections` | planned |
| M3 | Report writer: Pydantic schema, Markdown + YAML front-matter output | planned |

The CLI is installed and accepts arguments. The agent loop is not yet wired up — running `researchmate` currently prints a version banner and exits cleanly.

## Motivation

Most "research agents" are either giant frameworks (LangChain, AutoGPT) or require a paid search API (Bing, Serper). ResearchMate is intentionally tiny: ~400 lines of Python, zero paid dependencies beyond an Anthropic key, and fully auditable. It demonstrates agentic tool-use, prompt engineering, and structured output in a self-contained project.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        CLI  (typer)                      │
│                researchmate "your question"               │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    Agent Loop                            │
│          claude-sonnet-4-6  (tool-use mode)              │
│                                                          │
│   ┌────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│   │ web_search │  │ fetch_page  │  │extract_sections │  │
│   │ DuckDuckGo │  │ httpx + bs4 │  │  text chunker   │  │
│   │ HTML scrape│  │             │  │                 │  │
│   └────────────┘  └─────────────┘  └─────────────────┘  │
│                                                          │
│   Iterates until evidence is sufficient or MAX_STEPS     │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                  Report Writer                           │
│   Pydantic schema → Markdown + YAML front-matter         │
│   saved to  ./reports/<slug>.md                          │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yourusername/researchmate-web-agent.git
cd researchmate-web-agent

# 2. Create a virtual environment (Python 3.11+)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install
pip install -e .

# 4. Configure
cp .env.example .env
# Edit .env and add your Anthropic API key

# 5. Run  (agent loop ships in M2 — currently prints a version banner)
researchmate "What are the best open-source vector databases in 2026?"
```

Reports are saved to `./reports/<slug>.md` once M3 is complete.

## Project Layout

```
researchmate-web-agent/
├── src/
│   └── researchmate/
│       ├── __init__.py       # package version
│       ├── cli.py            # typer CLI entry point
│       ├── agent.py          # Claude tool-use loop  (M2)
│       ├── tools.py          # web_search / fetch_page / extract_sections  (M2)
│       └── report.py         # Pydantic report schema + Markdown writer  (M3)
├── reports/                  # generated reports (git-ignored)
├── tests/                    # pytest suite
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
├── requirements-dev.txt
└── README.md
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `MAX_STEPS` | `10` | Max tool-call iterations per run |
| `MODEL` | `claude-sonnet-4-6` | Claude model ID |

## Roadmap

- **M2** — implement `agent.py` (tool-use loop, `MAX_STEPS` guard) and `tools.py` (`web_search` via DuckDuckGo HTML scrape, `fetch_page` via httpx + BeautifulSoup, `extract_sections` text chunker)
- **M3** — implement `report.py` (Pydantic `ResearchReport` schema, Markdown writer with YAML front-matter, save to `reports/<slug>.md`)
- **M4** — pytest suite covering tools (mocked HTTP) and report serialisation; CI with GitHub Actions
- **M5** — packaging polish: `--verbose` flag, `--format json` output, published to PyPI

<!-- TODO: add items here as the project grows -->

## License

MIT — see [LICENSE](LICENSE).
