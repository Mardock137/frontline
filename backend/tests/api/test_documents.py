"""Tests for the documents / RAG API endpoints (mocked dependencies)."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api import documents as documents_module
from database.models import DocumentStatus
from main import app
from rag.ingestion import IngestionResult
from rag.search import SearchResult
from utils import auth as auth_module
from utils.config import Settings


@pytest.fixture
def company_id():
    return uuid4()


@pytest.fixture
def client(monkeypatch, company_id):
    def fake_settings() -> Settings:
        return Settings(
            DEV_COMPANY_ID=str(company_id),
            ALLOW_DEV_COMPANY_FALLBACK=True,
        )

    monkeypatch.setattr(auth_module, "get_settings", fake_settings)
    return TestClient(app)


def test_upload_rejects_empty_file(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("faq.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_runs_ingestion(client, monkeypatch, company_id):
    called = {}
    doc_id = uuid4()

    async def fake_ingest(
        *, company_id, filename, content_type, data, embedding_client=None
    ):
        called["company_id"] = company_id
        called["filename"] = filename
        called["content_type"] = content_type
        called["data"] = data
        return IngestionResult(
            document_id=doc_id, chunk_count=3, status=DocumentStatus.READY
        )

    monkeypatch.setattr(documents_module, "ingest_document", fake_ingest)

    response = client.post(
        "/documents/upload",
        files={"file": ("faq.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"] == str(doc_id)
    assert body["chunk_count"] == 3
    assert body["status"] == "ready"
    assert called["company_id"] == company_id
    assert called["filename"] == "faq.txt"


def test_list_documents(client, monkeypatch, company_id):
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": str(uuid4()),
                "filename": "faq.pdf",
                "content_type": "application/pdf",
                "status": "ready",
                "created_at": "2026-04-21T10:00:00Z",
                "chunk_count": 7,
            }
        ]
    )
    monkeypatch.setattr(documents_module, "get_supabase_client", lambda: supabase)

    response = client.get("/documents")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["filename"] == "faq.pdf"
    assert body[0]["chunk_count"] == 7
    supabase.table.assert_called_with("documents_with_counts")


def test_delete_document_404_when_missing(client, monkeypatch):
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    monkeypatch.setattr(documents_module, "get_supabase_client", lambda: supabase)

    response = client.delete(f"/documents/{uuid4()}")
    assert response.status_code == 404


def test_delete_document_removes_storage_and_row(client, monkeypatch, company_id):
    doc_id = uuid4()
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {"storage_path": f"{company_id}/faq.pdf", "company_id": str(company_id)}
        ]
    )
    monkeypatch.setattr(documents_module, "get_supabase_client", lambda: supabase)

    response = client.delete(f"/documents/{doc_id}")

    assert response.status_code == 204
    supabase.storage.from_.assert_called_with("documents")
    supabase.storage.from_.return_value.remove.assert_called_once()
    delete_calls = [c for c in supabase.table.mock_calls if ".delete" in str(c)]
    assert delete_calls


def test_rag_search_returns_hits(client, monkeypatch):
    async def fake_search(*, query, company_id, top_k, embedding_client=None):
        return [
            SearchResult(
                chunk_id=uuid4(),
                document_id=uuid4(),
                chunk_index=0,
                content="Answer here.",
                similarity=0.92,
            )
        ]

    monkeypatch.setattr(documents_module, "search_chunks", fake_search)

    response = client.post(
        "/rag/search", json={"query": "How do I reset?", "top_k": 5}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["hits"]) == 1
    assert body["hits"][0]["content"] == "Answer here."


def test_rag_search_rejects_empty_query(client):
    response = client.post("/rag/search", json={"query": "", "top_k": 5})
    assert response.status_code == 422
