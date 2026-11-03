"""Tests for the document ingestion pipeline (fully mocked)."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from database.models import DocumentStatus
from integrations.embedding_interfaces.base_embedding_interface import (
    BaseEmbeddingInterface,
)
from rag import ingestion


class _FakeEmbedder(BaseEmbeddingInterface):
    def __init__(self, dimension: int = 1024) -> None:
        super().__init__(model="fake", dimension=dimension)
        self.calls: list[tuple[list[str], str]] = []

    async def embed(self, texts, *, input_type="document"):
        self.calls.append((list(texts), input_type))
        return [[0.1] * self.dimension for _ in texts]


def _make_fake_supabase(document_id: str) -> MagicMock:
    supabase = MagicMock()

    supabase.storage.from_.return_value.upload.return_value = None

    insert_exec = MagicMock()
    insert_exec.execute.return_value = MagicMock(data=[{"id": document_id}])
    supabase.table.return_value.insert.return_value = insert_exec

    update_chain = MagicMock()
    update_chain.eq.return_value.execute.return_value = MagicMock()
    supabase.table.return_value.update.return_value = update_chain

    return supabase


@pytest.fixture
def patched_clients(monkeypatch):
    doc_id = str(uuid4())
    supabase = _make_fake_supabase(doc_id)
    embedder = _FakeEmbedder()

    monkeypatch.setattr(ingestion, "get_supabase_client", lambda: supabase)
    return supabase, embedder, doc_id


async def test_ingest_txt_document_success(patched_clients):
    supabase, embedder, _ = patched_clients
    company_id = uuid4()

    result = await ingestion.ingest_document(
        company_id=company_id,
        filename="faq.txt",
        content_type="text/plain",
        data=b"This is a short FAQ content for testing.",
        embedding_client=embedder,
    )

    assert result.status is DocumentStatus.READY
    assert result.chunk_count == 1
    assert embedder.calls and embedder.calls[0][1] == "document"

    supabase.storage.from_.assert_called_with(ingestion.STORAGE_BUCKET)
    insert_calls = [c for c in supabase.table.mock_calls if "document_chunks" in str(c)]
    assert insert_calls, "document_chunks insert should have been called"


async def test_ingest_sets_error_when_no_text(patched_clients):
    _, embedder, _ = patched_clients

    result = await ingestion.ingest_document(
        company_id=uuid4(),
        filename="empty.txt",
        content_type="text/plain",
        data=b"   \n\t ",
        embedding_client=embedder,
    )

    assert result.status is DocumentStatus.ERROR
    assert result.chunk_count == 0
    assert embedder.calls == []


async def test_ingest_sets_error_when_storage_upload_fails(patched_clients):
    supabase, embedder, doc_id = patched_clients
    supabase.storage.from_.return_value.upload.side_effect = RuntimeError("upload failed")

    with pytest.raises(RuntimeError, match="upload failed"):
        await ingestion.ingest_document(
            company_id=uuid4(),
            filename="faq.txt",
            content_type="text/plain",
            data=b"This is a short FAQ content for testing.",
            embedding_client=embedder,
        )

    update_calls = supabase.table.return_value.update.call_args_list
    assert any(call.args[0] == {"status": DocumentStatus.ERROR.value} for call in update_calls)
    assert embedder.calls == []


async def test_ingest_sanitizes_filename_in_storage_path(patched_clients):
    supabase, embedder, _ = patched_clients
    company_id = uuid4()

    await ingestion.ingest_document(
        company_id=company_id,
        filename="../../../secret.txt",
        content_type="text/plain",
        data=b"This is a short FAQ content for testing.",
        embedding_client=embedder,
    )

    upload_call = supabase.storage.from_.return_value.upload.call_args.kwargs
    assert ".." not in upload_call["path"]
    assert upload_call["path"].endswith("/secret.txt")
