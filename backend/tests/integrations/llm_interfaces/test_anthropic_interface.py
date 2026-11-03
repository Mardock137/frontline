"""Tests for AnthropicInterface (YAML config and Anthropic SDK mocked)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import integrations.llm_interfaces.anthropic_interface as anthropic_module
from config.llm_models.loader import LLMModelConfig
from integrations.llm_interfaces.anthropic_interface import AnthropicInterface
from integrations.llm_interfaces.base_llm_interface import ChatResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config(monkeypatch):
    """Replace load_model_config so it never touches the filesystem."""
    cfg = LLMModelConfig(model="claude-test-model", max_tokens=512, effort="medium")
    monkeypatch.setattr(anthropic_module, "load_model_config", lambda name: cfg)
    return cfg


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Replace AsyncAnthropic so no real HTTP calls are made."""
    client = MagicMock()
    monkeypatch.setattr(anthropic_module.anthropic, "AsyncAnthropic", lambda api_key: client)
    return client


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


def test_init_loads_model_from_yaml(mock_config, mock_anthropic_client):
    iface = AnthropicInterface(api_key="fake-key")
    assert iface.model == "claude-test-model"
    assert iface._default_max_tokens == 512
    assert iface._effort == "medium"


def test_init_effort_override_takes_precedence(mock_config, mock_anthropic_client):
    iface = AnthropicInterface(api_key="fake-key", effort="low")
    assert iface._effort == "low"


def test_init_model_override_takes_precedence(mock_config, mock_anthropic_client):
    iface = AnthropicInterface(api_key="fake-key", model="claude-override")
    assert iface.model == "claude-override"


def test_init_max_tokens_override_takes_precedence(mock_config, mock_anthropic_client):
    iface = AnthropicInterface(api_key="fake-key", max_tokens=2048)
    assert iface._default_max_tokens == 2048


def test_init_raises_without_api_key(mock_config, mock_anthropic_client, monkeypatch):
    monkeypatch.setattr(
        anthropic_module, "get_settings", lambda: MagicMock(ANTHROPIC_API_KEY="")
    )
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        AnthropicInterface(api_key="")


def test_init_uses_api_key_from_settings(mock_config, monkeypatch):
    created_with = {}

    def fake_async_anthropic(api_key):
        created_with["api_key"] = api_key
        return MagicMock()

    monkeypatch.setattr(anthropic_module.anthropic, "AsyncAnthropic", fake_async_anthropic)
    monkeypatch.setattr(
        anthropic_module, "get_settings", lambda: MagicMock(ANTHROPIC_API_KEY="from-env")
    )

    AnthropicInterface()
    assert created_with["api_key"] == "from-env"


# ---------------------------------------------------------------------------
# chat() — uses max_tokens from config by default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_uses_default_max_tokens_from_config(mock_config, mock_anthropic_client):
    text_block = MagicMock(type="text", text="Hello!")
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            stop_reason="end_turn",
            content=[text_block],
        )
    )

    iface = AnthropicInterface(api_key="fake-key")
    await iface.chat([{"role": "user", "content": "Hi"}])

    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["max_tokens"] == 512  # from mock_config


@pytest.mark.asyncio
async def test_chat_passes_output_config_with_effort(mock_config, mock_anthropic_client):
    text_block = MagicMock(type="text", text="Hello!")
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            stop_reason="end_turn",
            content=[text_block],
        )
    )

    iface = AnthropicInterface(api_key="fake-key")
    await iface.chat([{"role": "user", "content": "Hi"}])

    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["output_config"] == {"effort": "medium"}  # from mock_config


@pytest.mark.asyncio
async def test_chat_uses_overridden_effort(mock_config, mock_anthropic_client):
    text_block = MagicMock(type="text", text="Hello!")
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            stop_reason="end_turn",
            content=[text_block],
        )
    )

    iface = AnthropicInterface(api_key="fake-key", effort="low")
    await iface.chat([{"role": "user", "content": "Hi"}])

    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["output_config"] == {"effort": "low"}


@pytest.mark.asyncio
async def test_chat_uses_explicit_max_tokens_when_provided(mock_config, mock_anthropic_client):
    text_block = MagicMock(type="text", text="Hello!")
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            stop_reason="end_turn",
            content=[text_block],
        )
    )

    iface = AnthropicInterface(api_key="fake-key")
    await iface.chat([{"role": "user", "content": "Hi"}], max_tokens=256)

    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["max_tokens"] == 256


@pytest.mark.asyncio
async def test_chat_returns_text_response(mock_config, mock_anthropic_client):
    text_block = MagicMock(type="text", text="Hello!")
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(stop_reason="end_turn", content=[text_block])
    )

    iface = AnthropicInterface(api_key="fake-key")
    response = await iface.chat([{"role": "user", "content": "Hello"}])

    assert isinstance(response, ChatResponse)
    assert response.stop_reason == "end_turn"
    assert response.text == "Hello!"
    assert response.tool_uses == []


@pytest.mark.asyncio
async def test_chat_concatenates_multiple_text_blocks(
    mock_config, mock_anthropic_client
):
    first_text_block = MagicMock(type="text", text="First part")
    second_text_block = MagicMock(type="text", text="Second part")
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            stop_reason="end_turn",
            content=[first_text_block, second_text_block],
        )
    )

    iface = AnthropicInterface(api_key="fake-key")
    response = await iface.chat([{"role": "user", "content": "Hello"}])

    assert response.text == "First part\nSecond part"
    assert response.raw_content == [
        {"type": "text", "text": "First part"},
        {"type": "text", "text": "Second part"},
    ]


@pytest.mark.asyncio
async def test_chat_returns_tool_use_response(mock_config, mock_anthropic_client):
    # `name` is reserved on MagicMock (it sets the internal repr), so set it
    # as a separate attribute after creation.
    tool_block = MagicMock(type="tool_use", id="tool_1", input={"query": "test"})
    tool_block.name = "search_knowledge"
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(stop_reason="tool_use", content=[tool_block])
    )

    iface = AnthropicInterface(api_key="fake-key")
    response = await iface.chat(
        [{"role": "user", "content": "search something"}],
        tools=[{"name": "search_knowledge", "description": "...", "input_schema": {}}],
    )

    assert response.stop_reason == "tool_use"
    assert len(response.tool_uses) == 1
    assert response.tool_uses[0].name == "search_knowledge"
    assert response.tool_uses[0].input == {"query": "test"}


# ---------------------------------------------------------------------------
# get_llm_client factory
# ---------------------------------------------------------------------------


def test_get_llm_client_returns_anthropic_interface(mock_config, mock_anthropic_client, monkeypatch):
    monkeypatch.setattr(
        anthropic_module, "get_settings", lambda: MagicMock(ANTHROPIC_API_KEY="fake")
    )

    from integrations.llm_interfaces.anthropic_interface import get_llm_client

    client = get_llm_client()
    assert isinstance(client, AnthropicInterface)
