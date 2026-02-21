# Architecture Overview

This document explains how web-automator works from end to end. It is intended for developers who want to understand the internals before contributing.

## High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│  Entry Points                                                │
│  cli.py (Typer)  or  server.py (FastAPI)                     │
└──────────┬───────────────────────────────┬───────────────────┘
           │                               │
           ▼                               ▼
     build_provider()               build_provider()
     (agent.py)                     (agent.py)
           │                               │
           ▼                               ▼
  ┌─────────────────────────────────────────────────┐
  │  Agent.run(task)                                │
  │                                                 │
  │  messages = [system_prompt, user_task]           │
  │                                                 │
  │  loop (up to max_steps):                        │
  │    ┌─────────────────────────────────┐          │
  │    │ provider.complete(messages,     │◄── tools │
  │    │                   tools)        │   from   │
  │    │         │                       │  tools.py│
  │    │         ▼                       │          │
  │    │   LLMResponse                   │          │
  │    │     ├─ content (text)           │          │
  │    │     └─ tool_calls[]             │          │
  │    └─────────────────────────────────┘          │
  │              │                                  │
  │              ▼                                  │
  │    ┌─────────────────────────────────────┐      │
  │    │ Dispatch each tool_call:            │      │
  │    │   "done"        → return result     │      │
  │    │   "list_skills" → skills.py         │      │
  │    │   "read_skill"  → skills.py         │      │
  │    │   "write_test"  → test_writer.py    │      │
  │    │    other        → browser.execute() │      │
  │    │                     │               │      │
  │    │                     ▼               │      │
  │    │               BrowserSession        │      │
  │    │               (Playwright)          │      │
  │    │                     │               │      │
  │    │                     ▼               │      │
  │    │              sites/try_auto_login() │      │
  │    │              (on navigate only)     │      │
  │    └─────────────────────────────────────┘      │
  │              │                                  │
  │              ▼                                  │
  │    append tool result to messages               │
  │    (repeat loop)                                │
  └─────────────────────────────────────────────────┘
```

## Component Summary

| Module | Purpose | Key Exports |
|---|---|---|
| `agent.py` | Orchestrates the LLM tool-use loop | `Agent`, `build_provider()`, `AgentResult`, `Step` |
| `browser.py` | Playwright session + action dispatcher | `BrowserSession`, `ToolResult`, `create_browser_session()` |
| `tools.py` | Tool schemas and validation | `TOOL_SCHEMAS`, `get_tool_schemas()`, `validate_tool_call()` |
| `providers/base.py` | Provider-neutral types | `LLMProvider`, `Message`, `ToolSchema`, `ToolCall`, `LLMResponse` |
| `providers/anthropic.py` | Anthropic Claude adapter | `AnthropicProvider` |
| `providers/openai.py` | OpenAI GPT adapter | `OpenAIProvider` |
| `sites/` | Deterministic login handlers | `try_auto_login()`, `SiteHandler` |
| `skills.py` | Markdown playbook discovery | `list_skills()`, `read_skill()` |
| `test_writer.py` | Writes generated test files to disk | `write_test()` |
| `cli.py` | Typer CLI (run task / start server) | `main()` |
| `server.py` | FastAPI HTTP API | `app` |

## Request Lifecycle

Here is what happens when you run:

```bash
python -m web_automator "go to example.com and get the title"
```

1. **Entry** — `__main__.py` calls `cli.main()`. Typer parses args and calls the root callback.

2. **Provider creation** — `build_provider()` reads `LLM_PROVIDER` from env (default `"anthropic"`), imports the matching provider class, and instantiates it with the selected model.

3. **Agent starts** — `Agent(provider).run(task)` is called inside `asyncio.run()`.

4. **Browser launch** — The agent creates a `BrowserSession` via `create_browser_session()`, which reads the `HEADLESS` env var. Playwright launches Chromium with a 1280x800 viewport.

5. **System prompt** — The agent builds a system prompt with instructions for the LLM. If skills are available on disk, a hint is appended.

6. **Conversation initialized** — `messages` starts as `[system_prompt, user_task]`.

7. **Agent loop** — For each step (up to `MAX_STEPS`):
   - Calls `provider.complete(messages, tools)` — the provider converts messages and tool schemas to its SDK format, calls the API, and normalizes the response back to `LLMResponse`.
   - Appends the assistant message (with any tool calls) to `messages`.
   - If no tool calls: the text response is treated as the final answer.
   - For each tool call: validates with `validate_tool_call()`, dispatches to the appropriate handler, records a `Step`, and appends the tool result to `messages` with the matching `tool_call_id`.
   - If the LLM called `done`: the loop exits and returns the result.

8. **Navigate + auto-login** — When the LLM calls `navigate`, `browser._navigate()` runs `page.goto()` then calls `try_auto_login(page)`. If a registered site handler matches, it logs in deterministically and appends a status note to the tool result.

9. **Cleanup** — The agent stops the browser in a `finally` block (only if it owns the session).

## Key Design Decisions

### Provider neutrality

All shared types (`Message`, `ToolCall`, `ToolSchema`, `LLMResponse`) are plain dataclasses in `providers/base.py`. Neither `agent.py` nor `tools.py` imports from `anthropic` or `openai`. Each provider module is the only place that touches SDK-specific types, converting to/from the shared format.

### Tool dispatch routing

Most tools go to `browser.execute_tool()`, but four are handled directly in the agent loop:
- `done` — signals task completion
- `list_skills` / `read_skill` — filesystem operations, no browser needed
- `write_test` — writes a file to disk

This keeps `browser.py` focused on Playwright actions only.

### Browser ownership

`Agent` tracks `_owns_browser`. If a `BrowserSession` is passed in (e.g., for testing), the agent skips `start()`/`stop()`. Otherwise, it fully owns the lifecycle.

### Auto-login as a transparent side-effect

The `sites/` system is invisible to the LLM. The login happens inside the `navigate` tool result, so the LLM sees it only as an informational note — it never needs to handle credentials.

### Skill injection

Skills are only mentioned in the system prompt if the skills directory contains playbooks. This keeps the prompt lean when no skills are present.
