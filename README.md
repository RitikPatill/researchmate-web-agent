# ResearchMate

A terminal-first autonomous research agent powered by Claude. Give it a question and it does the legwork: searches the web, reads pages, synthesises findings, and saves a structured Markdown report — no paid search API required.

## Status

| Milestone | Scope | State |
|---|---|---|
| **M1** | Repo scaffold: `src/` layout, pinned deps, CLI entry point stub, `.env.example`, MIT license | **done** |
| M2 | Agent loop: Claude tool-use, `web_search`, `fetch_page`, `extract_sections` | planned |
| M3 | Report writer: Pydantic schema, Markdown + YAML front-matter output | planned |
| M4 | pytest suite covering tools (mocked HTTP) and report serialisation; CI | planned |
| **M5** | `rich` Live display, CLI flags (`--max-steps`, `--model`, `--output-dir`, `--dry-run`), `.env` defaults | **done** |

**What works now (M1 + M5):**

- `researchmate <question> --dry-run` resolves the full configuration (model, step limit, output directory) and prints it as a Rich table — no API call made.
- `researchmate <question>` launches a `rich` Live display: an animated spinner showing the current step and tool name, a scrolling tool-call log table (step, tool, input snippet, result snippet, elapsed time), and a Markdown report preview panel on completion.
- All run parameters are configurable via CLI flags (`--max-steps`, `--model`, `--output-dir`) or `.env` variables (`MAX_STEPS`, `MODEL`); CLI flags take precedence.
- `agent.py` defines the `AgentCallback` structural protocol that `ResearchUI` satisfies, and stubs `agent.run()` — running without `--dry-run` exits with a yellow advisory until M2–M4 are implemented.

## Motivation

Most "research agents" are either giant frameworks (LangChain, AutoGPT) or require a paid search API (Bing, Serper). ResearchMate is intentionally tiny: ~400 lines of Python, zero paid dependencies beyond an Anthropic key, and fully auditable. It demonstrates agentic tool-use, prompt engineering, and structured output in a self-contained project.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│             CLI  (typer)  cli.py                         │
│   researchmate "question" [--max-steps N] [--model ID]   │
│                           [--output-dir DIR] [--dry-run] │
└──────────┬───────────────────────────┬───────────────────┘
           │                           │
           │ (live display)            │ (agent.run callback)
           ▼                           ▼
┌─────────────────────┐   ┌────────────────────────────────┐
│   ResearchUI        │   │         Agent Loop             │
│   ui.py             │◄──│   claude-sonnet-4-6            │
│                     │   │   (tool-use mode)              │
│  spinner            │   │                                │
│  tool-call log      │   │  ┌──────────┐  ┌───────────┐  │
│  report preview     │   │  │web_search│  │fetch_page │  │
└─────────────────────┘   │  │DuckDuckGo│  │httpx+bs4  │  │
                           │  └──────────┘  └───────────┘  │
                           │  ┌─────────────────────────┐  │
                           │  │    extract_sections     │  │
                           │  │      text chunker       │  │
                           │  └─────────────────────────┘  │
                           │  Iterates until MAX_STEPS      │
                           └───────────────┬────────────────┘
                                           │
                                           ▼
                           ┌────────────────────────────────┐
                           │        Report Writer           │
                           │  Pydantic schema → Markdown    │
                           │  + YAML front-matter           │
                           │  saved to <output-dir>/<slug>  │
                           └────────────────────────────────┘
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

# 5. Run
researchmate "What are the best open-source vector databases in 2026?"

# Dry-run (no API call — prints resolved config and exits)
researchmate "What are the best open-source vector databases in 2026?" --dry-run

# Custom flags
researchmate "question" --max-steps 15 --model claude-haiku-4-5-20251001 --output-dir ./out
```

The `rich` live display (spinner, tool-call log table) launches immediately. Reports are saved to `./reports/<slug>.md` once M2–M3 are complete.

## Project Layout

```
researchmate-web-agent/
├── src/
│   └── researchmate/
│       ├── __init__.py       # package version
│       ├── cli.py            # typer CLI (--max-steps, --model, --output-dir, --dry-run)
│       ├── ui.py             # ResearchUI: rich Live display, spinner, tool-call log, report preview
│       ├── agent.py          # AgentCallback protocol stub; run() raises NotImplementedError (M2)
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

- **M2** — implement `agent.py` (Claude tool-use loop, `MAX_STEPS` guard) and `tools.py` (`web_search` via DuckDuckGo HTML scrape, `fetch_page` via httpx + BeautifulSoup, `extract_sections` text chunker)
- **M3** — implement `report.py` (Pydantic `ResearchReport` schema, Markdown writer with YAML front-matter, save to `reports/<slug>.md`)
- **M4** — pytest suite covering tools (mocked HTTP) and report serialisation; CI with GitHub Actions
- **M6** — packaging polish: published to PyPI

<!-- TODO: add items here as the project grows -->

## License

MIT — see [LICENSE](LICENSE).
