"""Tests for agents/support_agent.py (all external calls mocked)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

import agents.support_agent as agent_module
from agents.support_agent import SupportAgent, _FALLBACK_REPLY
from database.models import AgentConfig, AgentTone, ConversationStatus
from integrations.llm_interfaces.base_llm_interface import ChatResponse, ToolUse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agent_config(company_id):
    return AgentConfig(
        id=uuid4(),
        company_id=company_id,
        agent_name="Frontline",
        company_display_name="Acme Corp",
        tone=AgentTone.FORMAL,
        default_language="it",
        updated_at="2026-01-01T00:00:00Z",
    )


@pytest.fixture
def supabase():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[]
    )
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])
    return sb


@pytest.fixture
def llm():
    return MagicMock()


@pytest.fixture
def support_agent(company_id, agent_config, llm, supabase):
    return SupportAgent(
        company_id=company_id,
        agent_config=agent_config,
        llm=llm,
        supabase=supabase,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text_response(text: str) -> ChatResponse:
    return ChatResponse(stop_reason="end_turn", text=text, tool_uses=[], raw_content=[])


def _tool_response(tool_name: str, tool_input: dict) -> ChatResponse:
    tool_id = "tool_abc123"
    raw = [{"type": "tool_use", "id": tool_id, "name": tool_name, "input": tool_input}]
    return ChatResponse(
        stop_reason="tool_use",
        text=None,
        tool_uses=[ToolUse(id=tool_id, name=tool_name, input=tool_input)],
        raw_content=raw,
    )


# ---------------------------------------------------------------------------
# Tests: run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_returns_direct_reply(support_agent, llm, conversation_id):
    llm.chat = AsyncMock(return_value=_text_response("Hi! How can I help you?"))

    result = await support_agent.run(
        {"conversation_id": conversation_id, "content": "Hi"}
    )

    assert result["reply"] == "Hi! How can I help you?"


@pytest.mark.asyncio
async def test_run_saves_messages_to_db(support_agent, llm, supabase, conversation_id):
    llm.chat = AsyncMock(return_value=_text_response("Agent reply."))

    await support_agent.run(
        {"conversation_id": conversation_id, "content": "Customer question."}
    )

    supabase.table.return_value.insert.assert_called()
    inserted = supabase.table.return_value.insert.call_args[0][0]
    roles = [r["role"] for r in inserted]
    assert "customer" in roles
    assert "agent" in roles


@pytest.mark.asyncio
async def test_run_with_knowledge_tool(
    support_agent, llm, supabase, monkeypatch, company_id, conversation_id
):
    async def fake_search_knowledge(query, *, company_id, **kwargs):
        return "[1] Answer from the KB."

    monkeypatch.setattr(agent_module.knowledge, "search_knowledge", fake_search_knowledge)

    llm.chat = AsyncMock(
        side_effect=[
            _tool_response("search_knowledge", {"query": "How do I reset?"}),
            _text_response("Here is the answer: [1] Answer from the KB."),
        ]
    )

    result = await support_agent.run(
        {"conversation_id": conversation_id, "content": "How do I reset?"}
    )

    assert result["reply"] == "Here is the answer: [1] Answer from the KB."
    assert llm.chat.call_count == 2


@pytest.mark.asyncio
async def test_run_with_ticket_tool(
    support_agent, llm, supabase, monkeypatch, conversation_id
):
    async def fake_create_ticket(
        subject, description, company_id, conversation_id, supabase
    ):
        return "Ticket created with ID: abc-123"

    monkeypatch.setattr(agent_module.ticket, "create_ticket", fake_create_ticket)

    llm.chat = AsyncMock(
        side_effect=[
            _tool_response("create_ticket", {"subject": "Bug", "description": "Details"}),
            _text_response("I opened a ticket for you."),
        ]
    )

    result = await support_agent.run(
        {"conversation_id": conversation_id, "content": "There's a bug"}
    )

    assert result["reply"] == "I opened a ticket for you."


@pytest.mark.asyncio
async def test_run_with_escalation_tool(
    support_agent, llm, supabase, monkeypatch, conversation_id
):
    async def fake_escalate(
        subject, description, company_id, conversation_id, supabase
    ):
        return "Conversation escalated."

    monkeypatch.setattr(agent_module.escalation, "escalate", fake_escalate)

    llm.chat = AsyncMock(
        side_effect=[
            _tool_response("escalate", {"subject": "Urgent", "description": "System down"}),
            _text_response("I escalated your request."),
        ]
    )

    result = await support_agent.run(
        {"conversation_id": conversation_id, "content": "Emergency!"}
    )

    assert result["reply"] == "I escalated your request."


@pytest.mark.asyncio
async def test_run_returns_fallback_on_max_iterations(support_agent, llm, monkeypatch, conversation_id):
    monkeypatch.setattr(agent_module, "_MAX_ITERATIONS", 2)

    async def fake_search_knowledge(query, *, company_id, **kwargs):
        return "result"

    monkeypatch.setattr(agent_module.knowledge, "search_knowledge", fake_search_knowledge)

    llm.chat = AsyncMock(
        return_value=_tool_response("search_knowledge", {"query": "loop"})
    )

    result = await support_agent.run(
        {"conversation_id": conversation_id, "content": "Loop"}
    )

    assert result["reply"] == _FALLBACK_REPLY


@pytest.mark.asyncio
async def test_run_unknown_tool_returns_final_reply(
    support_agent, llm, conversation_id
):
    llm.chat = AsyncMock(
        side_effect=[
            _tool_response("nonexistent_tool", {}),
            _text_response("Final reply."),
        ]
    )

    result = await support_agent.run(
        {"conversation_id": conversation_id, "content": "test"}
    )

    assert result["reply"] == "Final reply."
    assert llm.chat.call_count == 2


@pytest.mark.asyncio
async def test_execute_tool_returns_error_when_search_knowledge_query_missing(
    support_agent, conversation_id
):
    result = await support_agent._execute_tool(
        "search_knowledge", {}, conversation_id
    )

    assert "missing" in result


@pytest.mark.asyncio
async def test_execute_tool_returns_error_when_create_ticket_params_missing(
    support_agent, conversation_id
):
    result = await support_agent._execute_tool(
        "create_ticket", {}, conversation_id
    )

    assert "missing" in result


@pytest.mark.asyncio
async def test_execute_tool_returns_error_when_escalate_params_missing(
    support_agent, conversation_id
):
    result = await support_agent._execute_tool("escalate", {}, conversation_id)

    assert "missing" in result


@pytest.mark.asyncio
async def test_load_history_converts_roles(support_agent, supabase, conversation_id):
    supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[
            {"role": "customer", "content": "Hi"},
            {"role": "agent", "content": "Hi, how can I help you?"},
            {"role": "system", "content": "system note"},
        ]
    )

    history = await support_agent._load_history(conversation_id)

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hi"}
    assert history[1] == {"role": "assistant", "content": "Hi, how can I help you?"}
