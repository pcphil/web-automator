"""Anthropic (Claude) LLM provider."""

from __future__ import annotations

import os
from typing import Any

import anthropic

from web_automator.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    ToolCall,
    ToolSchema,
)

DEFAULT_MODEL = "claude-opus-4-6"


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        system_text, api_messages = self._convert_messages(messages)
        api_tools = [self._convert_tool(t) for t in tools]

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": api_messages,
        }
        if system_text:
            kwargs["system"] = system_text
        if api_tools:
            kwargs["tools"] = api_tools

        response = await self.client.messages.create(**kwargs)

        tool_calls: list[ToolCall] = []
        text_parts: list[str] = []

        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=block.input)
                )
            elif block.type == "text":
                text_parts.append(block.text)

        return LLMResponse(
            content="\n".join(text_parts) or None,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
        )

    def _convert_messages(
        self, messages: list[Message]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Split system message out, convert the rest to Anthropic format."""
        system_text = ""
        api_messages: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                system_text = msg.content if isinstance(msg.content, str) else ""
                continue

            if msg.role == "tool":
                # Tool results — must follow the assistant message that requested them
                api_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content
                                if isinstance(msg.content, str)
                                else str(msg.content),
                            }
                        ],
                    }
                )
                continue

            if msg.role == "assistant" and msg.tool_calls:
                # Build Anthropic content blocks: optional text + tool_use entries
                blocks: list[dict] = []
                if msg.content:
                    blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )
                api_messages.append({"role": "assistant", "content": blocks})
                continue

            api_messages.append(
                {
                    "role": msg.role,
                    "content": msg.content or "",
                }
            )

        return system_text, api_messages

    def _convert_tool(self, tool: ToolSchema) -> dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.parameters,
        }
