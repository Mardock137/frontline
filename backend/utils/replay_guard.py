"""Single-use registration of website SSO token ids on Upstash Redis."""

from __future__ import annotations

import logging

import httpx

from utils.config import get_settings

logger = logging.getLogger(__name__)

JTI_KEY_PREFIX = "support:sso-jti:"
JTI_TTL_SECONDS = 90
REQUEST_TIMEOUT_SECONDS = 3.0


class ReplayGuardUnavailable(Exception):
    """Upstash could not say whether this jti is new. Callers must fail closed."""


async def claim_jti(jti: str) -> bool:
    """Register ``jti`` if it has not been seen.

    Returns True when the id is new and was stored, False when it was already
    stored. Raises ``ReplayGuardUnavailable`` when the check cannot be completed.
    """
    settings = get_settings()
    base_url = settings.KV_REST_API_URL.strip().rstrip("/")
    token = settings.KV_REST_API_TOKEN.strip()
    if not base_url or not token:
        logger.error("SSO replay guard is not configured")
        raise ReplayGuardUnavailable("KV REST credentials are not configured")

    key = f"{JTI_KEY_PREFIX}{jti}"
    command = ["SET", key, "1", "NX", "EX", JTI_TTL_SECONDS]
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                base_url,
                headers={"Authorization": f"Bearer {token}"},
                json=command,
                follow_redirects=False,
            )
    except httpx.TimeoutException as exc:
        logger.exception("SSO replay guard timed out")
        raise ReplayGuardUnavailable("Upstash request timed out") from exc
    except httpx.HTTPError as exc:
        logger.exception("SSO replay guard request failed")
        raise ReplayGuardUnavailable("Upstash request failed") from exc

    if response.status_code < 200 or response.status_code >= 300:
        logger.error("SSO replay guard returned HTTP %s", response.status_code)
        raise ReplayGuardUnavailable(f"Upstash returned HTTP {response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        logger.exception("SSO replay guard returned an unreadable body")
        raise ReplayGuardUnavailable("Upstash response was not JSON") from exc

    if not isinstance(body, dict) or "result" not in body:
        logger.error("SSO replay guard returned an unexpected body")
        raise ReplayGuardUnavailable("Upstash response was missing result")

    result = body["result"]
    if result == "OK":
        return True
    if result is None:
        return False

    logger.error("SSO replay guard returned an unexpected result")
    raise ReplayGuardUnavailable("Upstash result was unexpected")
