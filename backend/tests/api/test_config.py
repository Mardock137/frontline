"""Tests for api/config.py endpoint (all external calls mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import api.config as config_module
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agent_config_row(company_id):
    return {
        "agent_name": "Sofia",
        "company_display_name": "Acme Srl",
        "logo_url": None,
        "primary_color": "#FF5733",
        "welcome_message": "Hi! How can I help you?",
    }


@pytest.fixture
def client():
    return TestClient(app)


def _make_supabase(company_id, agent_config_row):
    """Build a minimal Supabase mock covering all queries the endpoint makes."""
    supabase = MagicMock()

    def table_side_effect(name):
        tbl = MagicMock()
        if name == "companies":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": str(company_id)}]
            )
        elif name == "agent_configs":
            tbl.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[agent_config_row]
            )
        return tbl

    supabase.table.side_effect = table_side_effect
    return supabase


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_config_returns_branding(client, monkeypatch, company_id, agent_config_row):
    supabase = _make_supabase(company_id, agent_config_row)
    monkeypatch.setattr(config_module, "get_supabase_client", lambda: supabase)

    response = client.get("/chat/acme/config")

    assert response.status_code == 200
    body = response.json()
    assert body["agent_name"] == "Sofia"
    assert body["company_display_name"] == "Acme Srl"
    assert body["logo_url"] is None
    assert body["primary_color"] == "#FF5733"
    assert body["welcome_message"] == "Hi! How can I help you?"


def test_get_config_404_when_company_not_found(client, monkeypatch):
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    monkeypatch.setattr(config_module, "get_supabase_client", lambda: supabase)

    response = client.get("/chat/nonexistent/config")

    assert response.status_code == 404
    assert "nonexistent" in response.json()["detail"]


def test_get_config_404_when_agent_config_missing(client, monkeypatch, company_id):
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
    monkeypatch.setattr(config_module, "get_supabase_client", lambda: supabase)

    response = client.get("/chat/acme/config")

    assert response.status_code == 404
    assert "acme" in response.json()["detail"]


def test_get_config_with_logo_url(client, monkeypatch, company_id):
    agent_config_row_with_logo = {
        "agent_name": "Max",
        "company_display_name": "TechCorp",
        "logo_url": "https://example.com/logo.png",
        "primary_color": "#0000FF",
        "welcome_message": "Hello! How can I help?",
    }
    supabase = _make_supabase(company_id, agent_config_row_with_logo)
    monkeypatch.setattr(config_module, "get_supabase_client", lambda: supabase)

    response = client.get("/chat/techcorp/config")

    assert response.status_code == 200
    assert response.json()["logo_url"] == "https://example.com/logo.png"


def test_get_config_500_when_supabase_raises(monkeypatch):
    supabase = MagicMock()
    supabase.table.side_effect = RuntimeError("DB down")
    monkeypatch.setattr(config_module, "get_supabase_client", lambda: supabase)

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/chat/acme/config")

    assert response.status_code == 500
