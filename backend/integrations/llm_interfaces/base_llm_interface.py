"""Abstract interface for LLM providers.

Guarantees that every concrete LLM adapter (Anthropic, OpenAI, etc.) exposes
the same ``chat`` method, which supports both plain conversations and
tool-calling workflows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolUse:
    """A single tool invocation requested by the LLM."""

    id: str
    name: str
    input: dict


@dataclass
class ChatResponse:
    """Structured response from an LLM chat call.

    Attributes:
        stop_reason: Why the model stopped ("end_turn", "tool_use", etc.).
        text: The plain-text reply, populated when stop_reason is "end_turn".
        tool_uses: Tool invocations requested by the model.
        raw_content: The raw content blocks as returned by the provider,
            suitable for feeding back into the next messages turn.
    """

    stop_reason: str
    text: str | None = None
    tool_uses: list[ToolUse] = field(default_factory=list)
    raw_content: list[dict] = field(default_factory=list)


class BaseLLMInterface(ABC):
    """Uniform contract shared by every LLM integration."""

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        *,
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 1024,
    ) -> ChatResponse:
        """Send a chat turn and return a structured response.

        Args:
            messages: Conversation history. Each element is a dict with
                ``role`` ("user" or "assistant") and ``content`` (str or list
                of content blocks for tool results / multi-part turns).
            system: Optional system prompt.
            tools: Optional list of tool definitions in the provider's native
                format.
            max_tokens: Maximum number of tokens to generate.
        """
        raise NotImplementedError
