"""Anthropic Claude adapter implementing BaseLLMInterface.

Uses the official ``anthropic`` Python SDK (AsyncAnthropic) to support both
plain conversations and tool-calling workflows.

Model name and max_tokens are loaded from
``backend/config/llm_models/support_agent.yaml`` at instantiation time so that
changing them never requires touching Python code.
"""

from __future__ import annotations

import anthropic

from config.llm_models.loader import LLMModelConfig, load_model_config
from integrations.llm_interfaces.base_llm_interface import (
    BaseLLMInterface,
    ChatResponse,
    ToolUse,
)
from utils.config import get_settings

_DEFAULT_CONFIG_NAME = "support_agent"


class AnthropicInterface(BaseLLMInterface):
    """Concrete LLM adapter for Anthropic Claude.

    Model, max_tokens and effort defaults are read from the YAML config
    identified by ``config_name`` (defaults to ``"support_agent"``). All three
    can be overridden at instantiation time for testing or one-off calls.

    Args:
        api_key: Anthropic API key. Defaults to ``ANTHROPIC_API_KEY`` from
            Settings if not supplied.
        config_name: Name of the YAML file in ``config/llm_models/`` (without
            extension) to load model, max_tokens and effort from.
        model: Override for the model name. When ``None`` the value from the
            YAML config is used.
        max_tokens: Override for max_tokens. When ``None`` the value from the
            YAML config is used.
        effort: Override for the Claude effort level (``"low"``, ``"medium"``,
            ``"high"``, ``"xhigh"``, ``"max"``). When ``None`` the value from
            the YAML config is used.
    """

    def __init__(
        self,
        api_key: str | None = None,
        config_name: str = _DEFAULT_CONFIG_NAME,
        model: str | None = None,
        max_tokens: int | None = None,
        effort: str | None = None,
    ) -> None:
        cfg: LLMModelConfig = load_model_config(config_name)
        resolved_model = model if model is not None else cfg.model
        self._default_max_tokens = max_tokens if max_tokens is not None else cfg.max_tokens
        self._effort = effort if effort is not None else cfg.effort

        super().__init__(model=resolved_model)

        resolved_key = api_key or get_settings().ANTHROPIC_API_KEY
        if not resolved_key:
            raise RuntimeError(
                "Anthropic is not configured: set ANTHROPIC_API_KEY in backend/.env"
            )
        self._client = anthropic.AsyncAnthropic(api_key=resolved_key)

    async def chat(
        self,
        messages: list[dict],
        *,
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Call the Claude API and return a structured ChatResponse.

        Args:
            messages: Conversation history (user/assistant turns).
            system: Optional system prompt.
            tools: Optional list of tool definitions in Anthropic format.
            max_tokens: Maximum tokens to generate. Defaults to the value
                loaded from the YAML config.

        Returns:
            ChatResponse with text and/or tool_uses populated.
        """
        effective_max_tokens = max_tokens if max_tokens is not None else self._default_max_tokens

        kwargs: dict = {
            "model": self.model,
            "max_tokens": effective_max_tokens,
            "messages": messages,
        }
        if system is not None:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        kwargs["output_config"] = {"effort": self._effort}

        response = await self._client.messages.create(**kwargs)

        texts: list[str] = []
        tool_uses: list[ToolUse] = []
        raw_content: list[dict] = []

        for block in response.content:
            if block.type == "text":
                texts.append(block.text)
                raw_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_uses.append(
                    ToolUse(id=block.id, name=block.name, input=dict(block.input))
                )
                raw_content.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": dict(block.input),
                    }
                )

        return ChatResponse(
            stop_reason=response.stop_reason or "end_turn",
            text="\n".join(texts) if texts else None,
            tool_uses=tool_uses,
            raw_content=raw_content,
        )


def get_llm_client(
    config_name: str = _DEFAULT_CONFIG_NAME,
) -> AnthropicInterface:
    """Return a ready-to-use AnthropicInterface built from Settings and YAML config."""
    return AnthropicInterface(config_name=config_name)
