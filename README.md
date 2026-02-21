# web-automator

A Python + Playwright agent that accepts natural-language tasks, uses an LLM to reason about the page, and executes browser actions autonomously. Quickly prep Playwright test cases and scrape web pages.

## Features

- **Natural-language control** — describe what you want in plain English
- **Multi-provider LLM support** — Anthropic (Claude) or OpenAI (GPT-4o)
- **Playwright test generation** — agent inspects real DOM HTML to write reliable locators
- **Skills system** — reusable playbooks for common tasks (search, forms, GitHub navigation)
- **Auto-login for known sites** — deterministic login handlers keep credentials in `.env`, never sent to the LLM
- **CLI + HTTP API** — use from the terminal or integrate via REST

## Stack

- Python 3.11+ · Playwright · Anthropic SDK · OpenAI SDK · Typer · FastAPI

## Setup

```bash
pip install -e .
playwright install chromium
cp .env.example .env
# Add your API key(s) to .env
```

## Usage

### CLI

```bash
# Run a task (uses ANTHROPIC_API_KEY by default)
python -m web_automator "go to example.com and tell me the page title"

# With verbose step output
python -m web_automator --verbose "go to news.ycombinator.com and list the top 5 stories"

# Override provider / model
python -m web_automator --provider openai --model gpt-4o "search for Python on github.com"

# Generate a Playwright test
python -m web_automator --verbose "go to https://www.saucedemo.com and generate a Playwright test for the login page"

# Start the HTTP server
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

| Variable            | Default              | Description                                      |
|---------------------|----------------------|--------------------------------------------------|
| `LLM_PROVIDER`      | `anthropic`          | `anthropic` or `openai`                          |
| `LLM_MODEL`         | `claude-opus-4-6`    | Model ID                                         |
| `ANTHROPIC_API_KEY` | —                    | Required for Anthropic                           |
| `OPENAI_API_KEY`    | —                    | Required for OpenAI                              |
| `HEADLESS`          | `true`               | Run browser headlessly                           |
| `MAX_STEPS`         | `20`                 | Max agent loop iterations                        |
| `SKILLS_DIR`        | `./skills`           | Path to skills folder                            |
| `TESTS_DIR`         | `./generated_tests`  | Output directory for generated Playwright tests  |
| `SAUCEDEMO_USERNAME`| `standard_user`      | SauceDemo auto-login username                    |
| `SAUCEDEMO_PASSWORD`| `secret_sauce`       | SauceDemo auto-login password                    |

## Skills

Skills are markdown playbooks that guide the agent through common tasks. They live in `skills/` and are discovered recursively:

```
skills/
├── search/
│   └── google_search.md
├── navigation/
│   └── github.md
├── forms/
│   └── form_fill.md
└── testing/
    └── playwright_test.md
```

Drop a new `.md` file into any subdirectory and the agent will find it automatically via `list_skills`.

## Test Generation

The agent can write `pytest-playwright` test files to `generated_tests/`:

1. Agent calls `get_html` to inspect real DOM attributes
2. Picks reliable locators (`data-testid` → `aria-label` → `name` → `id` → text)
3. Writes a complete test file via `write_test`

Generated tests are excluded from version control (see `.gitignore`).

## Documentation

See the [`docs/`](docs/) directory for detailed guides:

- [Architecture Overview](docs/architecture.md) — data flow, component summary, request lifecycle
- [Adding a Provider](docs/adding-a-provider.md) — how to integrate a new LLM provider
- [Adding a Site Handler](docs/adding-a-site-handler.md) — how to add deterministic login for a new site
- [Tool Reference](docs/tools.md) — all 13 tools, dispatch routing, and how to add new ones

## Auto-Login

The `sites/` package contains deterministic login handlers that run via Playwright — no credentials are ever sent to the LLM. When the agent navigates to a known site, the handler automatically detects the login page, fills credentials from `.env`, and submits the form.

Currently supported sites:

| Site | Handler | Env vars |
|------|---------|----------|
| [saucedemo.com](https://www.saucedemo.com) | `SauceDemoHandler` | `SAUCEDEMO_USERNAME`, `SAUCEDEMO_PASSWORD` |

To add a new site, create a handler in `src/web_automator/sites/` that extends `SiteHandler` and register it in `sites/__init__.py`.

## Project Structure

```
web-automator/
├── skills/                    # Skill playbooks (markdown)
├── generated_tests/           # Output from write_test (git-ignored)
└── src/web_automator/
    ├── agent.py               # Core agentic loop
    ├── browser.py             # Playwright wrapper + action executor
    ├── tools.py               # Tool schemas
    ├── skills.py              # Skill loader (recursive discovery)
    ├── test_writer.py         # write_test utility
    ├── providers/             # LLM provider abstractions
    ├── sites/                 # Deterministic site login handlers
    │   ├── base.py            # SiteHandler ABC
    │   └── saucedemo.py       # SauceDemo handler
    ├── cli.py                 # Typer CLI
    └── server.py              # FastAPI server
```
