"""Tests for SSO site-token verification and Frontline session tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import utils.auth as auth_module
from utils.auth import (
    SITE_TOKEN_AUDIENCE,
    SITE_TOKEN_ISSUER,
    SITE_TOKEN_PRODUCT,
    SiteTokenClaims,
    create_session_token,
    get_current_company_id,
    verify_session_token,
    verify_site_token,
)
from utils.config import Settings

SSO_SECRET = "test-sso-shared-secret-at-least-32b"
SESSION_SECRET = "test-frontline-session-secret-32b"
COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
JTI = "22222222-2222-4222-8222-222222222222"


@pytest.fixture
def auth_settings(monkeypatch):
    settings = Settings(
        _env_file=None,
        SSO_SHARED_SECRET=SSO_SECRET,
        FRONTLINE_SESSION_SECRET=SESSION_SECRET,
        DEV_COMPANY_ID=str(COMPANY_ID),
        ALLOW_DEV_COMPANY_FALLBACK=True,
    )
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    return settings


def _site_token(
    *,
    company_id: UUID = COMPANY_ID,
    secret: str = SSO_SECRET,
    issuer: str = SITE_TOKEN_ISSUER,
    audience: str = SITE_TOKEN_AUDIENCE,
    exp_delta: timedelta = timedelta(seconds=60),
    include_sub: bool = True,
    sub: str | None = None,
    include_jti: bool = True,
    jti: str = JTI,
    include_product: bool = True,
    product: str = SITE_TOKEN_PRODUCT,
) -> str:
    now = datetime.now(UTC)
    payload: dict = {
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + exp_delta,
        "company_name": "Acme Srl",
    }
    if include_sub:
        payload["sub"] = sub if sub is not None else str(company_id)
    if include_jti:
        payload["jti"] = jti
    if include_product:
        payload["product"] = product
    return jwt.encode(payload, secret, algorithm="HS256")


def test_verify_site_token_valid(auth_settings):
    token = _site_token()
    assert verify_site_token(token) == SiteTokenClaims(company_id=COMPANY_ID, jti=JTI)


def test_verify_site_token_expired(auth_settings):
    token = _site_token(exp_delta=timedelta(seconds=-120))
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_site_token(token)


def test_verify_site_token_wrong_signature(auth_settings):
    token = _site_token(secret="wrong-secret-that-is-long-enough-32")
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_verify_site_token_missing_sub(auth_settings):
    token = _site_token(include_sub=False)
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_verify_site_token_invalid_sub(auth_settings):
    token = _site_token(sub="not-a-uuid")
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_verify_site_token_missing_jti(auth_settings):
    token = _site_token(include_jti=False)
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_verify_site_token_missing_product(auth_settings):
    token = _site_token(include_product=False)
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_verify_site_token_wrong_product(auth_settings):
    token = _site_token(product="other-product")
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_verify_site_token_wrong_issuer(auth_settings):
    token = _site_token(issuer="someone-else")
    with pytest.raises(jwt.InvalidTokenError):
        verify_site_token(token)


def test_create_and_verify_session_token(auth_settings):
    token = create_session_token(COMPANY_ID)
    assert verify_session_token(token) == COMPANY_ID


def test_get_current_company_id_fallback_dev(auth_settings):
    assert auth_settings.ALLOW_DEV_COMPANY_FALLBACK is True
    assert get_current_company_id(None) == COMPANY_ID


def test_get_current_company_id_rejects_missing_bearer_when_fallback_disabled(
    monkeypatch,
):
    settings = Settings(
        _env_file=None,
        FRONTLINE_SESSION_SECRET=SESSION_SECRET,
        DEV_COMPANY_ID=str(COMPANY_ID),
        ALLOW_DEV_COMPANY_FALLBACK=False,
    )
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    with pytest.raises(HTTPException) as exc_info:
        get_current_company_id(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required"


def test_get_current_company_id_bearer_works_when_fallback_disabled(monkeypatch):
    settings = Settings(
        _env_file=None,
        FRONTLINE_SESSION_SECRET=SESSION_SECRET,
        DEV_COMPANY_ID=str(COMPANY_ID),
        ALLOW_DEV_COMPANY_FALLBACK=False,
    )
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    token = create_session_token(COMPANY_ID)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert get_current_company_id(credentials) == COMPANY_ID


def test_get_current_company_id_ignores_dev_company_when_fallback_disabled(
    monkeypatch,
):
    settings = Settings(
        _env_file=None,
        DEV_COMPANY_ID=str(COMPANY_ID),
        ALLOW_DEV_COMPANY_FALLBACK=False,
    )
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    with pytest.raises(HTTPException) as exc_info:
        get_current_company_id(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required"


def test_get_current_company_id_from_bearer(auth_settings):
    token = create_session_token(COMPANY_ID)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert get_current_company_id(credentials) == COMPANY_ID


def test_get_current_company_id_invalid_bearer(auth_settings):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="not-a-valid-jwt"
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_company_id(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_company_id_missing_dev(monkeypatch):
    settings = Settings(
        _env_file=None,
        DEV_COMPANY_ID="",
        ALLOW_DEV_COMPANY_FALLBACK=True,
    )
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    with pytest.raises(HTTPException) as exc_info:
        get_current_company_id(None)
    assert exc_info.value.status_code == 500


def test_session_token_rejects_site_token(auth_settings):
    site = _site_token()
    with pytest.raises(jwt.InvalidTokenError):
        verify_session_token(site)


def test_create_session_token_uses_different_company(auth_settings):
    other = uuid4()
    token = create_session_token(other)
    assert verify_session_token(token) == other
