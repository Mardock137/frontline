"""Semantic search over a company's document chunks."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from database.supabase_client import get_supabase_client
from integrations.embedding_interfaces.base_embedding_interface import (
    BaseEmbeddingInterface,
)
from integrations.embedding_interfaces.voyage_embedding import get_embedding_client


@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    similarity: float


async def search_chunks(
    *,
    query: str,
    company_id: UUID,
    top_k: int = 5,
    embedding_client: BaseEmbeddingInterface | None = None,
) -> list[SearchResult]:
    """Return the top-K chunks most similar to ``query`` for the tenant."""
    if not query.strip():
        return []
    if top_k <= 0:
        return []

    embedder = embedding_client or get_embedding_client()
    supabase = get_supabase_client()

    query_embeddings = await embedder.embed([query], input_type="query")
    query_embedding = query_embeddings[0]

    response = await asyncio.to_thread(
        lambda: supabase.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_company_id": str(company_id),
                "match_count": top_k,
            },
        ).execute()
    )

    return [
        SearchResult(
            chunk_id=UUID(row["id"]),
            document_id=UUID(row["document_id"]),
            chunk_index=row["chunk_index"],
            content=row["content"],
            similarity=float(row["similarity"]),
        )
        for row in (response.data or [])
    ]
