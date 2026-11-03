"""Voyage AI embedding implementation.

Uses the Voyage REST API directly via ``httpx`` to avoid the ``voyageai``
SDK, which (as of 0.3.7) does not support Python 3.14.

API docs: https://docs.voyageai.com/reference/embeddings-api
"""

from functools import lru_cache

import httpx

from integrations.embedding_interfaces.base_embedding_interface import (
    BaseEmbeddingInterface,
)
from utils.config import get_settings

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL = "voyage-3"
DEFAULT_DIMENSION = 1024
DEFAULT_TIMEOUT = 60.0
# Voyage accepts at most 128 inputs per request on voyage-3.
MAX_BATCH_SIZE = 128


class VoyageEmbedding(BaseEmbeddingInterface):
    """Embedding adapter that calls the Voyage AI REST API."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        dimension: int = DEFAULT_DIMENSION,
        timeout: float = DEFAULT_TIMEOUT,
        batch_size: int = MAX_BATCH_SIZE,
    ) -> None:
        super().__init__(model=model, dimension=dimension)
        if not api_key:
            raise RuntimeError(
                "Voyage is not configured: set VOYAGE_API_KEY in backend/.env"
            )
        if batch_size <= 0 or batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"batch_size must be in (0, {MAX_BATCH_SIZE}]")
        self._api_key = api_key
        self._timeout = timeout
        self._batch_size = batch_size
        self._http_client = httpx.AsyncClient(timeout=self._timeout)

    async def embed(
        self,
        texts: list[str],
        *,
        input_type: str = "document",
    ) -> list[list[float]]:
        if not texts:
            return []
        if input_type not in ("document", "query"):
            raise ValueError("input_type must be 'document' or 'query'")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            payload = {
                "model": self.model,
                "input": batch,
                "input_type": input_type,
            }
            response = await self._http_client.post(
                VOYAGE_API_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()

            items = sorted(data["data"], key=lambda item: item["index"])
            all_vectors.extend(item["embedding"] for item in items)

        return all_vectors


@lru_cache(maxsize=1)
def get_embedding_client() -> BaseEmbeddingInterface:
    """Return a cached Voyage embedding client built from Settings."""
    settings = get_settings()
    return VoyageEmbedding(api_key=settings.VOYAGE_API_KEY)
