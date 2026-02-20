# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Web Automator** — a Python + Playwright agent that accepts natural-language tasks, uses an LLM to reason about the page, and executes browser actions autonomously.

## Stack

- **Python 3.11+** with `pyproject.toml` (hatchling build)
- **Playwright** for browser automation
- **Anthropic SDK** + **OpenAI SDK** behind a common `LLMProvider` abstraction
- **Typer** for CLI
- **FastAPI + uvicorn** for HTTP API
- **python-dotenv** for configuration

## Project Structure

```
web-automator/
├── pyproject.toml
├── .env.example
└── src/
    └── web_automator/
        ├── __init__.py
        ├── __main__.py       # python -m web_automator
        ├── agent.py          # Core agentic loop
        ├── browser.py        # Playwright wrapper + action executor
        ├── tools.py          # Tool schemas + dispatcher
        ├── providers/
        │   ├── __init__.py
        │   ├── base.py       # Abstract LLMProvider + shared types
        │   ├── anthropic.py  # Claude implementation
        │   └── openai.py     # OpenAI implementation
        ├── cli.py            # Typer CLI
        └── server.py         # FastAPI server
```

## Setup

```bash
pip install -e .
playwright install chromium
cp .env.example .env
# Edit .env and add your API key(s)
```

## Usage

### CLI

```bash
# Run a task (uses ANTHROPIC_API_KEY by default)
python -m web_automator "go to example.com and tell me the page title"

# With provider/model override
python -m web_automator --provider openai --model gpt-4o "search for Python on github.com"

# Verbose (shows each step)
python -m web_automator --verbose "go to news.ycombinator.com and list the top 5 stories"

# Start HTTP server
python -m web_automator serve
python -m web_automator serve --port 9000 --reload
```

### HTTP API

```bash
# Health check
curl http://localhost:8000/health

# Run a task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "go to example.com and return the page title"}'
```

## Configuration (`.env`)

| Variable            | Default           | Description               |
|---------------------|-------------------|---------------------------|
| `LLM_PROVIDER`      | `anthropic`       | `anthropic` or `openai`   |
| `LLM_MODEL`         | `claude-opus-4-6` | Model ID                  |
| `ANTHROPIC_API_KEY` | —                 | Required for Anthropic    |
| `OPENAI_API_KEY`    | —                 | Required for OpenAI       |
| `HEADLESS`          | `true`            | Run browser headlessly    |
| `MAX_STEPS`         | `20`              | Max agent loop iterations |

## Key Architecture Notes

- **`providers/base.py`** defines `Message`, `ToolSchema`, `ToolCall`, `LLMResponse` — provider-neutral types used throughout.
- **`tools.py`** defines all tool schemas once; both providers consume the same list.
- **`agent.py`** `build_provider()` factory instantiates the right provider from env/args.
- **`browser.py`** `BrowserSession.execute_tool()` dispatches tool names to Playwright calls.
- The agent stores assistant responses with full content blocks (text + tool_use) so conversation history round-trips correctly for both providers.
