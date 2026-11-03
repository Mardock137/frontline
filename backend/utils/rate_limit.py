"""Shared rate limiter instance for the FastAPI application.

A single module exposes the ``Limiter`` object so that both ``main.py``
(where it is registered on ``app.state``) and ``api/agent.py`` (where it
decorates the chat endpoint) can import it without creating circular
dependencies.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from utils.config import get_settings


def get_client_ip(request: Request) -> str:
    """Resolve the client IP used as the rate-limiting key.

    Behind a reverse proxy or load balancer the socket peer is the proxy,
    so every visitor would share a single bucket. When ``TRUST_PROXY_HEADERS``
    is enabled we instead read the original client from the leftmost entry of
    the ``X-Forwarded-For`` header.

    The header is honoured only when trust is explicitly enabled: trusting it
    without a proxy in front would let any client spoof its IP and bypass the
    limit on every request.
    """
    if get_settings().TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)
