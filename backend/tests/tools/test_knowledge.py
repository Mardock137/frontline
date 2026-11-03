"""Tests for tools/knowledge.py (all external calls mocked)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

import tools.knowledge as knowledge_module
from rag.search import SearchResult
from tools.knowledge import search_knowledge


@pytest.fixture
def company_id():
    return uuid4()


@pytest.mark.asyncio
async def test_search_knowledge_returns_formatted_results(monkeypatch, company_id):
    chunk1 = SearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        content="Answer to the question.",
        similarity=0.95,
    )
    chunk2 = SearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        chunk_index=1,
        content="Additional context.",
        similarity=0.88,
    )
    monkeypatch.setattr(
        knowledge_module, "search_chunks", AsyncMock(return_value=[chunk1, chunk2])
    )

    result = await search_knowledge("How do I reset?", company_id=company_id)

    assert "[1] Answer to the question." in result
    assert "[2] Additional context." in result


@pytest.mark.asyncio
async def test_search_knowledge_no_results(monkeypatch, company_id):
    monkeypatch.setattr(
        knowledge_module, "search_chunks", AsyncMock(return_value=[])
    )

    result = await search_knowledge("unknown question", company_id=company_id)

    assert "No results" in result


@pytest.mark.asyncio
async def test_search_knowledge_passes_query_and_company_id(monkeypatch, company_id):
    captured = {}

    async def fake_search(*, query, company_id, top_k, embedding_client):
        captured["query"] = query
        captured["company_id"] = company_id
        captured["top_k"] = top_k
        return []

    monkeypatch.setattr(knowledge_module, "search_chunks", fake_search)

    await search_knowledge("test query", company_id=company_id, top_k=3)

    assert captured["query"] == "test query"
    assert captured["company_id"] == company_id
    assert captured["top_k"] == 3


def test_tool_definition_has_required_fields():
    from tools.knowledge import TOOL_DEFINITION

    assert TOOL_DEFINITION["name"] == "search_knowledge"
    assert "description" in TOOL_DEFINITION
    assert "input_schema" in TOOL_DEFINITION
    schema = TOOL_DEFINITION["input_schema"]
    assert "query" in schema["properties"]
    assert "query" in schema["required"]
