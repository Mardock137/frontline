"""Tests for POST /auth/sso."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

import api.auth as auth_api
import utils.auth as auth_module
from main import app
from utils.auth import (
    SESSION_TOKEN_AUDIENCE,
    SESSION_TOKEN_ISSUER,
    SITE_TOKEN_AUDIENCE,
    SITE_TOKEN_ISSUER,
    SITE_TOKEN_PRODUCT,
    verify_session_token,
)
from utils.config import Settings
from utils.replay_guard import ReplayGuardUnavailable

SSO_SECRET = "test-sso-shared-secret-at-least-32b"
SESSION_SECRET = "test-frontline-session-secret-32b"
COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
JTI = "22222222-2222-4222-8222-222222222222"


class _MemoryReplayGuard:
    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.calls: list[str] = []
        self.unavailable = False

    async def __call__(self, jti: str) -> bool:
        self.calls.append(jti)
        if self.unavailable:
            raise ReplayGuardUnavailable("unavailable")
        if jti in self.seen:
            return False
        self.seen.add(jti)
        return True


@pytest.fixture
def guard(monkeypatch):
    memory = _MemoryReplayGuard()
    monkeypatch.setattr(auth_api, "claim_jti", memory)
    return memory


@pytest.fixture
def client(monkeypatch, guard):
    settings = Settings(
        _env_file=None,
        SSO_SHARED_SECRET=SSO_SECRET,
        FRONTLINE_SESSION_SECRET=SESSION_SECRET,
        DEV_COMPANY_ID=str(COMPANY_ID),
    )
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    return TestClient(app)


def _site_token(
    *,
    secret: str = SSO_SECRET,
    exp_delta: timedelta = timedelta(seconds=60),
    include_jti: bool = True,
    jti: str = JTI,
    include_product: bool = True,
    product: str = SITE_TOKEN_PRODUCT,
) -> str:
    now = datetime.now(UTC)
    payload: dict = {
        "sub": str(COMPANY_ID),
        "company_name": "Acme Srl",
        "iss": SITE_TOKEN_ISSUER,
        "aud": SITE_TOKEN_AUDIENCE,
        "iat": now,
        "exp": now + exp_delta,
    }
    if include_jti:
        payload["jti"] = jti
    if include_product:
        payload["product"] = product
    return jwt.encode(payload, secret, algorithm="HS256")


def test_sso_exchange_returns_session_token(client):
    response = client.post("/auth/sso", json={"sso_token": _site_token()})

    assert response.status_code == 200
    session_token = response.json()["session_token"]
    assert verify_session_token(session_token) == COMPANY_ID

    decoded = jwt.decode(
        session_token,
        SESSION_SECRET,
        algorithms=["HS256"],
        audience=SESSION_TOKEN_AUDIENCE,
        issuer=SESSION_TOKEN_ISSUER,
    )
    assert decoded["sub"] == str(COMPANY_ID)


def test_sso_exchange_rejects_expired_token(client, guard):
    response = client.post(
        "/auth/sso",
        json={"sso_token": _site_token(exp_delta=timedelta(seconds=-120))},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
    assert guard.calls == []


def test_sso_exchange_rejects_wrong_signature(client, guard):
    response = client.post(
        "/auth/sso",
        json={"sso_token": _site_token(secret="wrong-secret-that-is-long-enough-32")},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid SSO token"
    assert guard.calls == []


def test_sso_exchange_rejects_replay(client):
    token = _site_token()
    first = client.post("/auth/sso", json={"sso_token": token})
    second = client.post("/auth/sso", json={"sso_token": token})

    assert first.status_code == 200
    assert second.status_code == 401
    assert second.json()["detail"] == "Invalid SSO token"
    assert "session_token" not in second.json()


def test_sso_exchange_rejects_missing_jti(client, guard):
    response = client.post(
        "/auth/sso",
        json={"sso_token": _site_token(include_jti=False)},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid SSO token"
    assert guard.calls == []


def test_sso_exchange_rejects_wrong_product(client, guard):
    response = client.post(
        "/auth/sso",
        json={"sso_token": _site_token(product="other-product")},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid SSO token"
    assert guard.calls == []


def test_sso_exchange_guard_unavailable(client, guard):
    guard.unavailable = True
    response = client.post("/auth/sso", json={"sso_token": _site_token()})

    assert response.status_code == 503
    assert response.json()["detail"] == "SSO temporarily unavailable"
    assert "session_token" not in response.json()


def test_sso_exchange_rejects_empty_body(client):
    response = client.post("/auth/sso", json={"sso_token": ""})
    assert response.status_code == 422
