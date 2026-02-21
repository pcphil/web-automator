# Tool Reference

All tools are defined in `src/web_automator/tools.py` as `ToolSchema` objects. Both LLM providers consume the same list — each provider converts the schemas to its SDK format internally.

## Tool List

### Browser actions

| Tool | Required args | Optional args | Description |
|---|---|---|---|
| `navigate` | `url` | — | Go to a URL. Auto-upgrades HTTP to HTTPS. Triggers auto-login if a site handler matches. |
| `click` | `selector` | — | Click an element by CSS selector. Falls back to visible text match if CSS fails. |
| `type` | `selector`, `text` | — | Clear and fill an input field. |
| `scroll` | `direction` (`"up"` / `"down"`) | `amount` (px, default 500) | Scroll the page via `window.scrollBy()`. |
| `wait_for` | `selector` | `timeout` (ms, default 10000) | Wait for a CSS selector to appear in the DOM. |

### Page inspection

| Tool | Required args | Optional args | Description |
|---|---|---|---|
| `screenshot` | — | — | Capture viewport as base64 PNG. |
| `get_page_content` | — | — | Return page title + visible text (scripts/styles stripped, truncated to 8000 chars). |
| `get_html` | — | `selector` | Return raw HTML of the full page or a scoped element (truncated to 60000 chars). |
| `extract` | `description` | — | Wrapper around `get_page_content` — the LLM does the extraction from its context. |

### Task lifecycle

| Tool | Required args | Optional args | Description |
|---|---|---|---|
| `done` | `result` | — | Signal task completion and return the final answer. |

### Skills

| Tool | Required args | Optional args | Description |
|---|---|---|---|
| `list_skills` | — | — | List available skill playbook names. |
| `read_skill` | `name` | — | Read a skill playbook by name (e.g., `"search/google_search"`). |

### Test generation

| Tool | Required args | Optional args | Description |
|---|---|---|---|
| `write_test` | `filename`, `content` | — | Write a pytest-playwright test file to the `generated_tests/` directory. |

## Tool Dispatch

Tools are dispatched in two places:

**`agent.py`** handles these directly (no browser needed):
- `done` — captures the result and exits the loop
- `list_skills` — calls `skills.list_skills()`
- `read_skill` — calls `skills.read_skill(name)`
- `write_test` — calls `test_writer.write_test(filename, content)`

**`browser.py`** handles everything else via `BrowserSession.execute_tool()`, which uses a `match`/`case` dispatch to route tool names to private methods (`_navigate`, `_click`, `_type`, etc.).

## Validation

Before dispatch, `validate_tool_call(name, arguments)` in `tools.py` checks:
1. The tool name exists in `TOOL_SCHEMA_MAP`
2. All required arguments (from the JSON Schema) are present

If validation fails, the error string is returned to the LLM as the tool result so it can self-correct.

## Adding a new tool

1. Add a `ToolSchema` to the `TOOL_SCHEMAS` list in `src/web_automator/tools.py`
2. If it's a browser action: add a `case` branch and private method in `src/web_automator/browser.py`
3. If it's a non-browser action: add an `elif` branch in the dispatch section of `Agent.run()` in `src/web_automator/agent.py`
