"""Abstract LLM provider interface and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | None
    tool_calls: list["ToolCall"] | None = None  # populated for role="assistant" with tool use
    tool_call_id: str | None = None  # for role="tool"
    name: str | None = None  # tool name for role="tool"


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema object


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        """Send messages + tool schemas to the LLM and return its response."""
        ...
