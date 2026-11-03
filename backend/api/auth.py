"""SSO exchange: website JWT in, Frontline session token out."""

from __future__ import annotations

import logging

import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from utils.auth import create_session_token, verify_site_token
from utils.replay_guard import ReplayGuardUnavailable, claim_jti

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")


class SsoRequest(BaseModel):
    sso_token: str = Field(min_length=1)


class SsoResponse(BaseModel):
    session_token: str


@router.post("/sso", response_model=SsoResponse)
async def exchange_sso_token(body: SsoRequest) -> SsoResponse:
    """Verify the website SSO token once and return an internal session token."""
    try:
        claims = verify_site_token(body.sso_token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSO token has expired",
        ) from exc
    except jwt.PyJWTError as exc:
        logger.info("SSO token rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SSO token",
        ) from exc

    try:
        is_new = await claim_jti(claims.jti)
    except ReplayGuardUnavailable as exc:
        logger.exception("SSO replay guard unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SSO temporarily unavailable",
        ) from exc

    if not is_new:
        logger.info("SSO token rejected: already used")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SSO token",
        )

    try:
        session_token = create_session_token(claims.company_id)
    except RuntimeError as exc:
        logger.exception("Session token could not be created")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session secret is not configured",
        ) from exc

    return SsoResponse(session_token=session_token)
