# Adding a New LLM Provider

This guide walks through adding support for a new LLM provider (e.g., Google Gemini, Mistral, a local model).

## Steps

### 1. Create the provider module

Create `src/web_automator/providers/your_provider.py`:

```python
"""YourProvider LLM implementation."""

from __future__ import annotations

import os

from web_automator.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    ToolCall,
    ToolSchema,
)


class YourProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LLM_MODEL", "default-model-id")
        self.client = ...  # initialize your SDK client

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        # 1. Convert messages to your SDK's format
        # 2. Convert tool schemas to your SDK's format
        # 3. Call the API
        # 4. Parse the response back into LLMResponse
        ...
```

### 2. Understand the shared types

All types are defined in `src/web_automator/providers/base.py`:

| Type | Purpose |
|---|---|
| `Message` | A conversation turn (`role`, `content`, `tool_calls`, `tool_call_id`, `name`) |
| `ToolSchema` | Tool definition (`name`, `description`, `parameters` as JSON Schema) |
| `ToolCall` | A tool invocation from the LLM (`id`, `name`, `arguments` as parsed dict) |
| `LLMResponse` | The LLM's reply (`content`, `tool_calls`, `stop_reason`) |

### 3. Handle message conversion

Every provider needs to convert `Message` objects to its SDK format. The tricky parts are:

**System messages** — Anthropic extracts them and passes as a separate `system=` kwarg. OpenAI keeps them inline as `role="system"`. Check your SDK's convention.

**Tool result messages** — These have `role="tool"`, a `tool_call_id` to match the request, and the result string in `content`. Anthropic converts these to `role="user"` with a `tool_result` content block. OpenAI keeps them as `role="tool"`.

**Assistant messages with tool calls** — The `tool_calls` field contains `ToolCall` objects. Anthropic serializes these as content blocks (`type="tool_use"`). OpenAI uses a `tool_calls` array with `function.arguments` as a JSON string.

Look at the existing implementations for reference:
- `src/web_automator/providers/anthropic.py` — `_convert_messages()` and `_convert_tool()`
- `src/web_automator/providers/openai.py` — message and tool conversion in `complete()`

### 4. Register in the provider factory

In `src/web_automator/agent.py`, add an `elif` branch to `build_provider()`:

```python
def build_provider(provider_name: str | None = None, model: str | None = None) -> LLMProvider:
    name = (provider_name or os.getenv("LLM_PROVIDER", "anthropic")).lower()
    if name == "anthropic":
        from web_automator.providers.anthropic import AnthropicProvider
        return AnthropicProvider(model=model)
    elif name == "openai":
        from web_automator.providers.openai import OpenAIProvider
        return OpenAIProvider(model=model)
    elif name == "your_provider":
        from web_automator.providers.your_provider import YourProvider
        return YourProvider(model=model)
    else:
        raise ValueError(f"Unknown provider: {name!r}")
```

Note: imports are deferred (inside the branch) so unused SDK dependencies are never loaded.

### 5. Update configuration

Add your API key variable to `.env.example`:

```
YOUR_PROVIDER_API_KEY=your-key-here
```

### 6. Test it

```bash
python -m web_automator --provider your_provider --model your-model \
  "go to example.com and tell me the page title"
```

Verify that:
- The agent completes the task and returns a result
- Tool calls round-trip correctly (check with `--verbose`)
- Multi-turn conversations work (the LLM sees its own prior tool calls and results)
