"""Tests for the Supabase client factory."""

import pytest

from database import supabase_client
from database.supabase_client import get_supabase_client
from utils.config import Settings


@pytest.fixture(autouse=True)
def _clear_client_cache():
    """Clear cached client and settings between tests."""
    get_supabase_client.cache_clear()
    yield
    get_supabase_client.cache_clear()


def test_get_supabase_client_raises_when_not_configured(monkeypatch):
    def fake_settings() -> Settings:
        return Settings(SUPABASE_URL="", SUPABASE_SERVICE_ROLE_KEY="")

    monkeypatch.setattr(supabase_client, "get_settings", fake_settings)

    with pytest.raises(RuntimeError, match="Supabase is not configured"):
        get_supabase_client()


def test_get_supabase_client_builds_and_caches(monkeypatch):
    def fake_settings() -> Settings:
        return Settings(
            SUPABASE_URL="https://example.supabase.co",
            SUPABASE_SERVICE_ROLE_KEY="test-service-role-key",
        )

    monkeypatch.setattr(supabase_client, "get_settings", fake_settings)

    client_a = get_supabase_client()
    client_b = get_supabase_client()

    assert client_a is client_b
    assert client_a is not None
