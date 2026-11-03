"""Tests for api/agent.py endpoint (all external calls mocked)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import api.agent as agent_module
import utils.rate_limit as rate_limit_module
from main import app
from utils.config import Settings


@pytest.fixture
def agent_config_row(company_id):
    return {
        "id": str(uuid4()),
        "company_id": str(company_id),
        "agent_name": "Frontline",
        "company_display_name": "Acme Corp",
        "logo_url": None,
        "primary_color": "#000000",
        "tone": "formal",
        "default_language": "it",
        "welcome_message": "Hello!",
        "updated_at": "2026-01-01T00:00:00Z",
    }


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "get_settings",
        lambda: Settings(ANTHROPIC_API_KEY="test-key"),
    )
    return TestClient(app)


def _make_supabase(company_id, conversation_id, agent_config_row):
    """Build a minimal Supabase mock covering all queries the endpoint makes."""
    supabase = MagicMock()
    tables: dict[str, MagicMock] = {}

    def table_side_effect(name):
        if name in tables:
            return tables[name]

        tbl = MagicMock()
        if name == "companies":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(company_id)}]
            )
        elif name == "agent_configs":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[agent_config_row]
            )
        elif name == "conversations":
            tbl.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": str(conversation_id)}]
            )
            conversation_query = tbl.select.return_value.eq.return_value.eq.return_value
            conversation_query.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(conversation_id)}]
            )
        elif name == "messages":
            tbl.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[]
            )
            tbl.insert.return_value.execute.return_value = MagicMock(data=[])
        tables[name] = tbl
        return tbl

    supabase.table.side_effect = table_side_effect
    return supabase


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_send_message_creates_new_conversation(
    client, monkeypatch, company_id, conversation_id, agent_config_row
):
    supabase = _make_supabase(company_id, conversation_id, agent_config_row)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(
        agent_module, "get_llm_client", lambda **kw: MagicMock()
    )

    async def fake_run(self, input_data):
        return {"reply": "Agent reply."}

    monkeypatch.setattr(agent_module.SupportAgent, "run", fake_run)

    response = client.post(
        "/chat/acme/message",
        json={"content": "Hello"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == str(conversation_id)
    assert body["reply"] == "Agent reply."


def test_send_message_reuses_existing_conversation(
    client, monkeypatch, company_id, conversation_id, agent_config_row
):
    supabase = _make_supabase(company_id, conversation_id, agent_config_row)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(
        agent_module, "get_llm_client", lambda **kw: MagicMock()
    )

    async def fake_run(self, input_data):
        return {"reply": "Ok."}

    monkeypatch.setattr(agent_module.SupportAgent, "run", fake_run)

    response = client.post(
        "/chat/acme/message",
        json={"conversation_id": str(conversation_id), "content": "Another question"},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == str(conversation_id)


def test_send_message_404_when_conversation_belongs_to_other_company(
    client, monkeypatch, company_id, conversation_id, agent_config_row
):
    supabase = _make_supabase(company_id, conversation_id, agent_config_row)
    supabase.table("conversations").select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(
        agent_module, "get_llm_client", lambda **kw: MagicMock()
    )

    fake_run = AsyncMock(return_value={"reply": "Should not run"})
    monkeypatch.setattr(agent_module.SupportAgent, "run", fake_run)

    response = client.post(
        "/chat/acme/message",
        json={"conversation_id": str(conversation_id), "content": "Another question"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"
    fake_run.assert_not_awaited()


def test_send_message_404_when_company_not_found(
    client, monkeypatch, company_id, conversation_id, agent_config_row
):
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.post("/chat/nonexistent/message", json={"content": "Hello"})

    assert response.status_code == 404


def test_send_message_404_when_agent_config_missing(
    client, monkeypatch, company_id, conversation_id, agent_config_row
):
    supabase = MagicMock()

    def table_side_effect(name):
        tbl = MagicMock()
        if name == "companies":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(company_id)}]
            )
        elif name == "agent_configs":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[]
            )
        return tbl

    supabase.table.side_effect = table_side_effect
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.post("/chat/acme/message", json={"content": "Hello"})

    assert response.status_code == 404


def test_send_message_rejects_empty_content(
    client, monkeypatch, company_id, conversation_id, agent_config_row
):
    monkeypatch.setattr(
        agent_module, "get_supabase_client", lambda: MagicMock()
    )

    response = client.post("/chat/acme/message", json={"content": ""})

    assert response.status_code == 422


def test_send_message_500_when_api_key_missing(
    monkeypatch, company_id, conversation_id, agent_config_row
):
    monkeypatch.setattr(
        agent_module,
        "get_settings",
        lambda: Settings(ANTHROPIC_API_KEY=""),
    )
    supabase = _make_supabase(company_id, conversation_id, agent_config_row)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    test_client = TestClient(app)
    response = test_client.post("/chat/acme/message", json={"content": "Hello"})

    assert response.status_code == 500


def test_send_message_500_when_agent_raises(
    monkeypatch, company_id, conversation_id, agent_config_row
):
    monkeypatch.setattr(
        agent_module,
        "get_settings",
        lambda: Settings(ANTHROPIC_API_KEY="test-key"),
    )
    supabase = _make_supabase(company_id, conversation_id, agent_config_row)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(
        agent_module, "get_llm_client", lambda **kw: MagicMock()
    )

    async def failing_run(self, input_data):
        raise RuntimeError("LLM exploded")

    monkeypatch.setattr(agent_module.SupportAgent, "run", failing_run)

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.post("/chat/acme/message", json={"content": "Hello"})

    assert response.status_code == 500


def test_send_message_429_when_rate_limit_exceeded(
    monkeypatch, company_id, conversation_id, agent_config_row
):
    """Past the limit the backend returns 429 without calling the agent."""
    monkeypatch.setattr(
        agent_module,
        "get_settings",
        lambda: Settings(ANTHROPIC_API_KEY="test-key", CHAT_RATE_LIMIT="2/minute"),
    )
    supabase = _make_supabase(company_id, conversation_id, agent_config_row)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(agent_module, "get_llm_client", lambda **kw: MagicMock())

    agent_run = AsyncMock(return_value={"reply": "ok"})
    monkeypatch.setattr(agent_module.SupportAgent, "run", agent_run)

    rate_limit_module.limiter.enabled = True
    rate_limit_module.limiter._storage.reset()

    try:
        test_client = TestClient(app, raise_server_exceptions=False)

        test_client.post("/chat/acme/message", json={"content": "First"})
        test_client.post("/chat/acme/message", json={"content": "Second"})

        calls_before_limit = agent_run.await_count

        response = test_client.post("/chat/acme/message", json={"content": "Third"})

        assert response.status_code == 429
        # The agent must not be called for the request blocked by the rate limiter.
        assert agent_run.await_count == calls_before_limit
    finally:
        rate_limit_module.limiter.enabled = False
        rate_limit_module.limiter._storage.reset()


# ---------------------------------------------------------------------------
# Tests — GET /chat/{slug}/conversation/{id}/messages
# ---------------------------------------------------------------------------


def _make_supabase_messages(company_id, conversation_id, messages_data):
    """Build a Supabase mock for the GET messages endpoint."""
    supabase = MagicMock()

    def table_side_effect(name):
        tbl = MagicMock()
        if name == "companies":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(company_id)}]
            )
        elif name == "conversations":
            conv_query = tbl.select.return_value.eq.return_value.eq.return_value
            conv_query.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(conversation_id)}]
            )
        elif name == "messages":
            tbl.select.return_value.eq.return_value.neq.return_value.order.return_value.execute.return_value = MagicMock(
                data=messages_data
            )
        return tbl

    supabase.table.side_effect = table_side_effect
    return supabase


def test_get_messages_returns_messages_in_order(
    client, monkeypatch, company_id, conversation_id
):
    msg_id_1 = uuid4()
    msg_id_2 = uuid4()
    messages_data = [
        {"id": str(msg_id_1), "role": "customer", "content": "Hello"},
        {"id": str(msg_id_2), "role": "agent", "content": "How can I help you?"},
    ]
    supabase = _make_supabase_messages(company_id, conversation_id, messages_data)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.get(f"/chat/acme/conversation/{conversation_id}/messages")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["role"] == "customer"
    assert body[0]["content"] == "Hello"
    assert body[1]["role"] == "agent"
    assert body[1]["content"] == "How can I help you?"


def test_get_messages_returns_empty_list_when_no_messages(
    client, monkeypatch, company_id, conversation_id
):
    supabase = _make_supabase_messages(company_id, conversation_id, [])
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.get(f"/chat/acme/conversation/{conversation_id}/messages")

    assert response.status_code == 200
    assert response.json() == []


def test_get_messages_returns_empty_list_when_data_is_none(
    client, monkeypatch, company_id, conversation_id
):
    """If Supabase returns data=None the endpoint responds with an empty list, not 500."""
    supabase = _make_supabase_messages(company_id, conversation_id, None)
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.get(f"/chat/acme/conversation/{conversation_id}/messages")

    assert response.status_code == 200
    assert response.json() == []


def test_get_messages_404_when_company_not_found(
    client, monkeypatch, company_id, conversation_id
):
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.get(f"/chat/nonexistent/conversation/{conversation_id}/messages")

    assert response.status_code == 404


def test_get_messages_404_when_conversation_not_found(
    client, monkeypatch, company_id, conversation_id
):
    supabase = MagicMock()

    def table_side_effect(name):
        tbl = MagicMock()
        if name == "companies":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(company_id)}]
            )
        elif name == "conversations":
            conv_query = tbl.select.return_value.eq.return_value.eq.return_value
            conv_query.limit.return_value.execute.return_value = MagicMock(data=[])
        return tbl

    supabase.table.side_effect = table_side_effect
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.get(f"/chat/acme/conversation/{conversation_id}/messages")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_get_messages_404_when_conversation_belongs_to_other_company(
    client, monkeypatch, company_id, conversation_id
):
    other_company_id = uuid4()
    supabase = MagicMock()

    def table_side_effect(name):
        tbl = MagicMock()
        if name == "companies":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(other_company_id)}]
            )
        elif name == "conversations":
            conv_query = tbl.select.return_value.eq.return_value.eq.return_value
            conv_query.limit.return_value.execute.return_value = MagicMock(data=[])
        return tbl

    supabase.table.side_effect = table_side_effect
    monkeypatch.setattr(agent_module, "get_supabase_client", lambda: supabase)

    response = client.get(f"/chat/acme/conversation/{conversation_id}/messages")

    assert response.status_code == 404
