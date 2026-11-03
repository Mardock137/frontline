"""Tests for the Settings loader."""

from utils.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")
    monkeypatch.setenv("DEV_COMPANY_ID", "dev-id")
    monkeypatch.setenv("SSO_SHARED_SECRET", "sso-secret")
    monkeypatch.setenv("FRONTLINE_SESSION_SECRET", "session-secret")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.ANTHROPIC_API_KEY == "test-anthropic-key"
    assert settings.SUPABASE_URL == "https://test.supabase.co"
    assert settings.SUPABASE_ANON_KEY == "anon-key"
    assert settings.SUPABASE_SERVICE_ROLE_KEY == "service-key"
    assert settings.DEV_COMPANY_ID == "dev-id"
    assert settings.SSO_SHARED_SECRET == "sso-secret"
    assert settings.FRONTLINE_SESSION_SECRET == "session-secret"
    assert settings.LOG_LEVEL == "DEBUG"


def test_get_settings_is_cached():
    assert get_settings() is get_settings()
