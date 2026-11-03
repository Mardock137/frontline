"""Tests for the RAG search module (fully mocked)."""

from unittest.mock import MagicMock
from uuid import uuid4

from integrations.embedding_interfaces.base_embedding_interface import (
    BaseEmbeddingInterface,
)
from rag import search


class _FakeEmbedder(BaseEmbeddingInterface):
    def __init__(self) -> None:
        super().__init__(model="fake", dimension=1024)
        self.last_input_type: str | None = None

    async def embed(self, texts, *, input_type="document"):
        self.last_input_type = input_type
        return [[0.5] * self.dimension for _ in texts]


async def test_empty_query_returns_no_results():
    result = await search.search_chunks(
        query="   ", company_id=uuid4(), embedding_client=_FakeEmbedder()
    )
    assert result == []


async def test_search_calls_rpc_and_maps_results(monkeypatch):
    chunk_id = uuid4()
    doc_id = uuid4()
    company_id = uuid4()

    supabase = MagicMock()
    supabase.rpc.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": str(chunk_id),
                "document_id": str(doc_id),
                "chunk_index": 2,
                "content": "Relevant chunk.",
                "similarity": 0.87,
            }
        ]
    )
    monkeypatch.setattr(search, "get_supabase_client", lambda: supabase)

    embedder = _FakeEmbedder()

    results = await search.search_chunks(
        query="How do I reset my password?",
        company_id=company_id,
        top_k=3,
        embedding_client=embedder,
    )

    assert len(results) == 1
    assert results[0].chunk_id == chunk_id
    assert results[0].document_id == doc_id
    assert results[0].similarity == 0.87
    assert embedder.last_input_type == "query"

    supabase.rpc.assert_called_once()
    args, _ = supabase.rpc.call_args
    assert args[0] == "match_document_chunks"
    assert args[1]["match_company_id"] == str(company_id)
    assert args[1]["match_count"] == 3
