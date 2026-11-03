"""SSO from an external website and internal Frontline session tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils.config import get_settings

SITE_TOKEN_ISSUER = "partner-website"
SITE_TOKEN_AUDIENCE = "support-saas"
SITE_TOKEN_PRODUCT = "support-saas"
SITE_TOKEN_LEEWAY_SECONDS = 10

SESSION_TOKEN_ISSUER = "support-saas"
SESSION_TOKEN_AUDIENCE = "support-saas-session"
SESSION_TOKEN_TTL = timedelta(hours=24)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class SiteTokenClaims:
    """Identity carried by a verified website SSO token."""

    company_id: UUID
    jti: str


def verify_site_token(token: str) -> SiteTokenClaims:
    """Verify the website JWT and return the company id and token id."""
    settings = get_settings()
    if not settings.SSO_SHARED_SECRET:
        raise jwt.InvalidTokenError("SSO_SHARED_SECRET is not configured")

    payload = jwt.decode(
        token,
        settings.SSO_SHARED_SECRET,
        algorithms=["HS256"],
        audience=SITE_TOKEN_AUDIENCE,
        issuer=SITE_TOKEN_ISSUER,
        leeway=SITE_TOKEN_LEEWAY_SECONDS,
        options={"require": ["exp", "iat", "sub", "jti"]},
    )
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti.strip():
        raise jwt.InvalidTokenError("Token is missing the jti claim")
    if payload.get("product") != SITE_TOKEN_PRODUCT:
        raise jwt.InvalidTokenError("Token product claim is invalid")
    return SiteTokenClaims(company_id=_company_id_from_sub(payload), jti=jti)


def create_session_token(company_id: UUID) -> str:
    """Sign an internal session JWT valid for 24 hours."""
    settings = get_settings()
    if not settings.FRONTLINE_SESSION_SECRET:
        raise RuntimeError("FRONTLINE_SESSION_SECRET is not configured")

    now = datetime.now(UTC)
    payload = {
        "sub": str(company_id),
        "iss": SESSION_TOKEN_ISSUER,
        "aud": SESSION_TOKEN_AUDIENCE,
        "iat": now,
        "exp": now + SESSION_TOKEN_TTL,
    }
    return jwt.encode(payload, settings.FRONTLINE_SESSION_SECRET, algorithm="HS256")


def verify_session_token(token: str) -> UUID:
    """Verify an internal session JWT and return the company id."""
    settings = get_settings()
    if not settings.FRONTLINE_SESSION_SECRET:
        raise jwt.InvalidTokenError("FRONTLINE_SESSION_SECRET is not configured")

    payload = jwt.decode(
        token,
        settings.FRONTLINE_SESSION_SECRET,
        algorithms=["HS256"],
        audience=SESSION_TOKEN_AUDIENCE,
        issuer=SESSION_TOKEN_ISSUER,
    )
    return _company_id_from_sub(payload)


def get_current_company_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UUID:
    """Resolve the tenant from the session token.

    Without a Bearer token, ``DEV_COMPANY_ID`` is used only when
    ``ALLOW_DEV_COMPANY_FALLBACK`` is enabled. Otherwise the request is rejected.
    """
    if credentials is not None:
        try:
            return verify_session_token(credentials.credentials)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token",
            ) from exc

    if not get_settings().ALLOW_DEV_COMPANY_FALLBACK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return _dev_company_id()


def _company_id_from_sub(payload: dict) -> UUID:
    raw = payload.get("sub")
    if not raw:
        raise jwt.InvalidTokenError("Token is missing the sub claim")
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise jwt.InvalidTokenError("Token sub is not a valid UUID") from exc


def _dev_company_id() -> UUID:
    settings = get_settings()
    if not settings.DEV_COMPANY_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DEV_COMPANY_ID is not set",
        )
    try:
        return UUID(settings.DEV_COMPANY_ID)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DEV_COMPANY_ID is not a valid UUID",
        ) from exc
