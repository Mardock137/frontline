"""Tests for the Voyage embedding client (network is mocked via httpx)."""

import httpx
import pytest

from integrations.embedding_interfaces.voyage_embedding import (
    VOYAGE_API_URL,
    VoyageEmbedding,
)

_REAL_ASYNC_CLIENT = httpx.AsyncClient


def _patch_async_client(monkeypatch, handler):
    """Route all httpx.AsyncClient requests through the given handler.

    We must capture a reference to the real AsyncClient BEFORE patching,
    otherwise the replacement function ends up calling itself (infinite
    recursion), because ``voyage_embedding.httpx`` is the same module
    object as ``httpx`` imported here.
    """

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return _REAL_ASYNC_CLIENT(*args, **kwargs)

    monkeypatch.setattr(
        "integrations.embedding_interfaces.voyage_embedding.httpx.AsyncClient",
        fake_async_client,
    )


async def test_requires_api_key():
    with pytest.raises(RuntimeError, match="Voyage is not configured"):
        VoyageEmbedding(api_key="")


async def test_empty_input_returns_empty():
    client = VoyageEmbedding(api_key="key")
    assert await client.embed([]) == []


async def test_embed_returns_vectors_in_request_order(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.2] * 1024},
                    {"index": 0, "embedding": [0.1] * 1024},
                ],
                "model": "voyage-3",
            },
        )

    _patch_async_client(monkeypatch, handler)

    client = VoyageEmbedding(api_key="key")
    result = await client.embed(["hello", "world"], input_type="query")

    assert captured["url"] == VOYAGE_API_URL
    assert captured["auth"] == "Bearer key"
    assert len(result) == 2
    assert result[0][0] == pytest.approx(0.1)
    assert result[1][0] == pytest.approx(0.2)


async def test_invalid_input_type_raises():
    client = VoyageEmbedding(api_key="key")
    with pytest.raises(ValueError):
        await client.embed(["hi"], input_type="other")


async def test_embed_splits_into_batches(monkeypatch):
    received_batch_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content)
        received_batch_sizes.append(len(payload["input"]))
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": i, "embedding": [float(i)] * 1024}
                    for i in range(len(payload["input"]))
                ],
                "model": "voyage-3",
            },
        )

    _patch_async_client(monkeypatch, handler)

    client = VoyageEmbedding(api_key="key", batch_size=3)
    texts = [f"text-{i}" for i in range(7)]
    result = await client.embed(texts)

    assert len(result) == 7
    assert received_batch_sizes == [3, 3, 1]


async def test_http_error_is_raised(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    _patch_async_client(monkeypatch, handler)

    client = VoyageEmbedding(api_key="bad")
    with pytest.raises(httpx.HTTPStatusError):
        await client.embed(["hi"])
