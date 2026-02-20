"""Core agentic loop: LLM + browser + tools."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from web_automator.browser import BrowserSession, create_browser_session
from web_automator.providers.base import LLMProvider, LLMResponse, Message, ToolCall
from web_automator.skills import list_skills
from web_automator.skills import read_skill as _read_skill
from web_automator.test_writer import write_test as _write_test
from web_automator.tools import get_tool_schemas, validate_tool_call

SYSTEM_PROMPT = """\
You are a web automation agent. Your job is to complete tasks in a real browser.

You have access to tools that let you navigate pages, click elements, type text, \
take screenshots, and extract information. After each action you can observe the \
result and decide what to do next.

Guidelines:
- Break the task into small, concrete steps.
- Use `screenshot` or `get_page_content` to understand the current page state before acting.
- Prefer CSS selectors (e.g. `#id`, `.class`, `button[type=submit]`) over text selectors when possible.
- When you have completed the task and have a final answer, call the `done` tool with your result.
- If you cannot complete the task, call `done` with an explanation of what went wrong.
"""


@dataclass
class Step:
    step_number: int
    tool_name: str
    tool_args: dict[str, Any]
    tool_result: str
    success: bool


@dataclass
class AgentResult:
    result: str
    steps: list[Step] = field(default_factory=list)
    success: bool = True
    error: str | None = None


class Agent:
    def __init__(
        self,
        provider: LLMProvider,
        max_steps: int | None = None,
        browser: BrowserSession | None = None,
    ):
        self.provider = provider
        self.max_steps = max_steps or int(os.getenv("MAX_STEPS", "20"))
        self._browser = browser
        self._owns_browser = browser is None

    async def run(self, task: str) -> AgentResult:
        steps: list[Step] = []
        browser = self._browser or create_browser_session()

        try:
            if self._owns_browser:
                await browser.start()

            tools = get_tool_schemas()

            system_prompt = SYSTEM_PROMPT
            if list_skills():
                system_prompt += (
                    "\nSkills are available — call `list_skills` to see them or "
                    "`read_skill(name)` to load one before starting a task."
                )

            messages: list[Message] = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=task),
            ]

            for step_num in range(1, self.max_steps + 1):
                response: LLMResponse = await self.provider.complete(messages, tools)

                # Append assistant turn in provider-neutral format
                messages.append(
                    Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls if response.tool_calls else None,
                    )
                )

                if not response.tool_calls:
                    # LLM responded with plain text — treat as final answer
                    return AgentResult(
                        result=response.content or "(no response)",
                        steps=steps,
                        success=True,
                    )

                # Execute each tool call
                done_result: str | None = None
                for tool_call in response.tool_calls:
                    error = validate_tool_call(tool_call.name, tool_call.arguments)
                    if error:
                        tool_output = f"ERROR: {error}"
                        success = False
                    elif tool_call.name == "done":
                        done_result = tool_call.arguments["result"]
                        tool_output = done_result
                        success = True
                    elif tool_call.name == "list_skills":
                        skills = list_skills()
                        tool_output = ", ".join(skills) if skills else "(no skills found)"
                        success = True
                    elif tool_call.name == "read_skill":
                        tool_output = _read_skill(tool_call.arguments["name"])
                        success = True
                    elif tool_call.name == "write_test":
                        tool_output = _write_test(
                            tool_call.arguments["filename"],
                            tool_call.arguments["content"],
                        )
                        success = True
                    else:
                        result = await browser.execute_tool(
                            tool_call.name, tool_call.arguments
                        )
                        tool_output = result.error or result.output
                        success = result.success

                    steps.append(
                        Step(
                            step_number=step_num,
                            tool_name=tool_call.name,
                            tool_args=tool_call.arguments,
                            tool_result=tool_output[:500],  # cap for display
                            success=success,
                        )
                    )

                    # Add tool result to messages
                    messages.append(
                        Message(
                            role="tool",
                            content=tool_output,
                            tool_call_id=tool_call.id,
                            name=tool_call.name,
                        )
                    )

                if done_result is not None:
                    return AgentResult(result=done_result, steps=steps, success=True)

            return AgentResult(
                result="Max steps reached without completing the task.",
                steps=steps,
                success=False,
                error="max_steps_exceeded",
            )

        except Exception as exc:
            return AgentResult(
                result=f"Agent error: {exc}",
                steps=steps,
                success=False,
                error=str(exc),
            )
        finally:
            if self._owns_browser:
                await browser.stop()


def build_provider(provider_name: str | None = None, model: str | None = None) -> LLMProvider:
    """Instantiate the correct LLMProvider from env/args."""
    name = (provider_name or os.getenv("LLM_PROVIDER", "anthropic")).lower()
    if name == "anthropic":
        from web_automator.providers.anthropic import AnthropicProvider
        return AnthropicProvider(model=model)
    elif name == "openai":
        from web_automator.providers.openai import OpenAIProvider
        return OpenAIProvider(model=model)
    else:
        raise ValueError(f"Unknown provider: {name!r}. Choose 'anthropic' or 'openai'.")
