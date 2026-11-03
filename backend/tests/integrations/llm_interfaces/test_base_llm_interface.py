"""Tests for the BaseLLMInterface contract and ChatResponse/ToolUse dataclasses."""

from __future__ import annotations

import pytest

from integrations.llm_interfaces.base_llm_interface import (
    BaseLLMInterface,
    ChatResponse,
    ToolUse,
)


# ---------------------------------------------------------------------------
# Minimal concrete implementation for testing the abstract class
# ---------------------------------------------------------------------------


class _ConcreteInterface(BaseLLMInterface):
    async def chat(self, messages, *, system=None, tools=None, max_tokens=1024):
        return ChatResponse(stop_reason="end_turn", text="ok")


# ---------------------------------------------------------------------------
# BaseLLMInterface
# ---------------------------------------------------------------------------


def test_concrete_interface_initialises():
    iface = _ConcreteInterface(model="test-model")
    assert iface.model == "test-model"


@pytest.mark.asyncio
async def test_concrete_interface_chat_returns_chat_response():
    iface = _ConcreteInterface(model="test-model")
    response = await iface.chat([{"role": "user", "content": "hello"}])
    assert isinstance(response, ChatResponse)
    assert response.stop_reason == "end_turn"
    assert response.text == "ok"


def test_base_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseLLMInterface(model="x")  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# ChatResponse dataclass
# ---------------------------------------------------------------------------


def test_chat_response_defaults():
    r = ChatResponse(stop_reason="end_turn")
    assert r.text is None
    assert r.tool_uses == []
    assert r.raw_content == []


def test_chat_response_with_text():
    r = ChatResponse(stop_reason="end_turn", text="Hello!")
    assert r.text == "Hello!"


def test_chat_response_with_tool_uses():
    tool = ToolUse(id="t1", name="search_knowledge", input={"query": "test"})
    r = ChatResponse(stop_reason="tool_use", tool_uses=[tool])
    assert len(r.tool_uses) == 1
    assert r.tool_uses[0].name == "search_knowledge"


# ---------------------------------------------------------------------------
# ToolUse dataclass
# ---------------------------------------------------------------------------


def test_tool_use_fields():
    t = ToolUse(id="abc", name="create_ticket", input={"subject": "Bug"})
    assert t.id == "abc"
    assert t.name == "create_ticket"
    assert t.input == {"subject": "Bug"}
