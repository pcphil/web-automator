"""OpenAI LLM provider."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import AsyncOpenAI

from web_automator.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    ToolCall,
    ToolSchema,
)

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        api_messages = [self._convert_message(m) for m in messages]
        api_tools = [self._convert_tool(t) for t in tools]

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
        }
        if api_tools:
            kwargs["tools"] = api_tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "stop",
        )

    def _convert_message(self, msg: Message) -> dict[str, Any]:
        if msg.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "content": msg.content or "",
            }
        if msg.role == "assistant" and msg.tool_calls:
            return {
                "role": "assistant",
                "content": msg.content,  # may be None — OpenAI accepts null
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        return {
            "role": msg.role,
            "content": msg.content or "",
        }

    def _convert_tool(self, tool: ToolSchema) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
