"""Tests for the dashboard API endpoints.

All Supabase calls are mocked via monkeypatch (same pattern as the rest of the
test suite).  No real network or database access is needed.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import api.dashboard as dashboard_module
import utils.auth as auth_module
from main import app

# ---------------------------------------------------------------------------
# Stable test data
# ---------------------------------------------------------------------------

COMPANY_ID = "11111111-1111-1111-1111-111111111111"
TICKET_ID = "22222222-2222-2222-2222-222222222222"
CONVERSATION_ID = "33333333-3333-3333-3333-333333333333"

TICKET_ROW = {
    "id": TICKET_ID,
    "conversation_id": CONVERSATION_ID,
    "subject": "Test subject",
    "description": "Test description",
    "status": "open",
    "is_escalation": False,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
}

AGENT_CONFIG_ROW = {
    "agent_name": "Frontline",
    "company_display_name": "Acme Srl",
    "primary_color": "#FF5733",
    "tone": "formal",
    "default_language": "it",
    "welcome_message": "Hi!",
}

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(monkeypatch):
    """TestClient with the local company fallback enabled."""
    mock_settings = MagicMock()
    mock_settings.DEV_COMPANY_ID = COMPANY_ID
    mock_settings.ALLOW_DEV_COMPANY_FALLBACK = True
    monkeypatch.setattr(auth_module, "get_settings", lambda: mock_settings)
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /dashboard/tickets
# ---------------------------------------------------------------------------


def test_list_tickets_returns_list(client, monkeypatch):
    mock_response = MagicMock()
    mock_response.data = [TICKET_ROW]

    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .order.return_value
        .execute.return_value
    ) = mock_response

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.get("/dashboard/tickets")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["subject"] == "Test subject"
    assert data[0]["is_escalation"] is False


def test_list_tickets_empty(client, monkeypatch):
    mock_response = MagicMock()
    mock_response.data = []

    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .order.return_value
        .execute.return_value
    ) = mock_response

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.get("/dashboard/tickets")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tickets_500_when_supabase_raises(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.DEV_COMPANY_ID = COMPANY_ID
    mock_settings.ALLOW_DEV_COMPANY_FALLBACK = True
    monkeypatch.setattr(auth_module, "get_settings", lambda: mock_settings)

    mock_sb = MagicMock()
    mock_sb.table.side_effect = RuntimeError("DB down")
    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/dashboard/tickets")

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# PATCH /dashboard/tickets/{ticket_id}
# ---------------------------------------------------------------------------


def test_update_ticket_status_success(client, monkeypatch):
    updated_row = {**TICKET_ROW, "status": "in_progress"}

    mock_sb = MagicMock()
    # First query: ownership check
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = [{"company_id": COMPANY_ID}]
    # Second query: update
    (
        mock_sb.table.return_value
        .update.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) = [updated_row]

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.patch(
        f"/dashboard/tickets/{TICKET_ID}",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_ticket_status_not_found(client, monkeypatch):
    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = []

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.patch(
        f"/dashboard/tickets/{TICKET_ID}",
        json={"status": "closed"},
    )

    assert response.status_code == 404


def test_update_ticket_status_wrong_company(client, monkeypatch):
    other_company = str(uuid.uuid4())

    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = [{"company_id": other_company}]

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.patch(
        f"/dashboard/tickets/{TICKET_ID}",
        json={"status": "closed"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /dashboard/agent-config
# ---------------------------------------------------------------------------


def test_get_agent_config_success(client, monkeypatch):
    mock_response = MagicMock()
    mock_response.data = [AGENT_CONFIG_ROW]

    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
    ) = mock_response

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.get("/dashboard/agent-config")

    assert response.status_code == 200
    data = response.json()
    assert data["agent_name"] == "Frontline"
    assert data["tone"] == "formal"


def test_get_agent_config_not_found(client, monkeypatch):
    mock_response = MagicMock()
    mock_response.data = []

    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
    ) = mock_response

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.get("/dashboard/agent-config")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /dashboard/agent-config
# ---------------------------------------------------------------------------


def test_update_agent_config_success(client, monkeypatch):
    updated_row = {**AGENT_CONFIG_ROW, "agent_name": "Nova", "tone": "informal"}

    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .update.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) = [updated_row]

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.patch(
        "/dashboard/agent-config",
        json={"agent_name": "Nova", "tone": "informal"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["agent_name"] == "Nova"
    assert data["tone"] == "informal"


def test_update_agent_config_empty_body(client):
    response = client.patch("/dashboard/agent-config", json={})
    assert response.status_code == 422


def test_update_agent_config_not_found(client, monkeypatch):
    mock_sb = MagicMock()
    (
        mock_sb.table.return_value
        .update.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) = []

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.patch(
        "/dashboard/agent-config",
        json={"agent_name": "Nova"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /dashboard/stats
# ---------------------------------------------------------------------------


def test_get_stats_requires_auth_without_fallback(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.DEV_COMPANY_ID = COMPANY_ID
    mock_settings.ALLOW_DEV_COMPANY_FALLBACK = False
    monkeypatch.setattr(auth_module, "get_settings", lambda: mock_settings)

    response = TestClient(app).get("/dashboard/stats")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_get_stats_success(client, monkeypatch):
    conv_response = MagicMock()
    conv_response.count = 42

    open_response = MagicMock()
    open_response.count = 2

    in_progress_response = MagicMock()
    in_progress_response.count = 1

    closed_response = MagicMock()
    closed_response.count = 2

    escalation_open_response = MagicMock()
    escalation_open_response.count = 2

    conv_mock = MagicMock()
    (
        conv_mock
        .select.return_value
        .eq.return_value
        .execute.return_value
    ) = conv_response

    open_mock = MagicMock()
    (
        open_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = open_response

    in_progress_mock = MagicMock()
    (
        in_progress_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = in_progress_response

    closed_mock = MagicMock()
    (
        closed_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = closed_response

    escalation_open_mock = MagicMock()
    (
        escalation_open_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .neq.return_value
        .execute.return_value
    ) = escalation_open_response

    mock_sb = MagicMock()
    mock_sb.table.side_effect = [
        conv_mock,
        open_mock,
        in_progress_mock,
        closed_mock,
        escalation_open_mock,
    ]

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.get("/dashboard/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_conversations"] == 42
    assert data["tickets_by_status"]["open"] == 2
    assert data["tickets_by_status"]["in_progress"] == 1
    assert data["tickets_by_status"]["closed"] == 2
    assert data["escalation_open_count"] == 2


def test_get_stats_no_data(client, monkeypatch):
    conv_response = MagicMock()
    conv_response.count = 0

    open_response = MagicMock()
    open_response.count = 0

    in_progress_response = MagicMock()
    in_progress_response.count = 0

    closed_response = MagicMock()
    closed_response.count = 0

    escalation_open_response = MagicMock()
    escalation_open_response.count = 0

    conv_mock = MagicMock()
    (
        conv_mock
        .select.return_value
        .eq.return_value
        .execute.return_value
    ) = conv_response

    open_mock = MagicMock()
    (
        open_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = open_response

    in_progress_mock = MagicMock()
    (
        in_progress_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = in_progress_response

    closed_mock = MagicMock()
    (
        closed_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = closed_response

    escalation_open_mock = MagicMock()
    (
        escalation_open_mock
        .select.return_value
        .eq.return_value
        .eq.return_value
        .neq.return_value
        .execute.return_value
    ) = escalation_open_response

    mock_sb = MagicMock()
    mock_sb.table.side_effect = [
        conv_mock,
        open_mock,
        in_progress_mock,
        closed_mock,
        escalation_open_mock,
    ]

    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: mock_sb)

    response = client.get("/dashboard/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_conversations"] == 0
    assert data["tickets_by_status"] == {"open": 0, "in_progress": 0, "closed": 0}
    assert data["escalation_open_count"] == 0
