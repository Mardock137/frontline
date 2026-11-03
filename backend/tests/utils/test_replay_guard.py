"""Tests for the SSO jti replay guard. No real Upstash calls."""

from __future__ import annotations

import json

import httpx
import pytest

import utils.replay_guard as replay_guard
from utils.config import Settings
from utils.replay_guard import ReplayGuardUnavailable, claim_jti

KV_URL = "https://kv.example.test"
KV_TOKEN = "test-kv-token"
JTI = "22222222-2222-4222-8222-222222222222"
EXPECTED_KEY = f"support:sso-jti:{JTI}"

_REAL_ASYNC_CLIENT = httpx.AsyncClient


@pytest.fixture
def kv_settings(monkeypatch):
    settings = Settings(
        _env_file=None,
        KV_REST_API_URL=KV_URL,
        KV_REST_API_TOKEN=KV_TOKEN,
    )
    monkeypatch.setattr(replay_guard, "get_settings", lambda: settings)
    return settings


def _patch_async_client(monkeypatch, handler, captured: dict | None = None):
    def fake_async_client(*args, **kwargs):
        if captured is not None:
            captured["timeout"] = kwargs.get("timeout")
        kwargs["transport"] = httpx.MockTransport(handler)
        return _REAL_ASYNC_CLIENT(*args, **kwargs)

    monkeypatch.setattr(replay_guard.httpx, "AsyncClient", fake_async_client)


async def test_claim_jti_new_sends_set_nx(kv_settings, monkeypatch):
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["authorization"]
        captured["command"] = json.loads(request.content)
        return httpx.Response(200, json={"result": "OK"})

    _patch_async_client(monkeypatch, handler, captured)

    assert await claim_jti(JTI) is True
    assert captured["url"] == KV_URL
    assert captured["authorization"] == f"Bearer {KV_TOKEN}"
    assert captured["timeout"] == replay_guard.REQUEST_TIMEOUT_SECONDS
    assert captured["command"] == ["SET", EXPECTED_KEY, "1", "NX", "EX", 90]


async def test_claim_jti_already_used(kv_settings, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": None})

    _patch_async_client(monkeypatch, handler)

    assert await claim_jti(JTI) is False


async def test_claim_jti_http_error(kv_settings, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "unavailable"})

    _patch_async_client(monkeypatch, handler)

    with pytest.raises(ReplayGuardUnavailable):
        await claim_jti(JTI)


async def test_claim_jti_timeout(kv_settings, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    _patch_async_client(monkeypatch, handler)

    with pytest.raises(ReplayGuardUnavailable):
        await claim_jti(JTI)


@pytest.mark.parametrize(
    ("url", "token"),
    [
        ("", KV_TOKEN),
        ("   ", KV_TOKEN),
        (KV_URL, ""),
        (KV_URL, "   "),
    ],
)
async def test_claim_jti_missing_config(monkeypatch, url, token):
    settings = Settings(
        _env_file=None,
        KV_REST_API_URL=url,
        KV_REST_API_TOKEN=token,
    )
    monkeypatch.setattr(replay_guard, "get_settings", lambda: settings)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Upstash must not be called when config is missing")

    monkeypatch.setattr(replay_guard.httpx, "AsyncClient", fail_if_called)

    with pytest.raises(ReplayGuardUnavailable):
        await claim_jti(JTI)
