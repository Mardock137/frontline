"""HTTP endpoints for documents and RAG search.

The tenant comes from the Frontline session token (``Authorization: Bearer``).
Without a token the request is rejected, unless ``ALLOW_DEV_COMPANY_FALLBACK``
is enabled (local development), in which case ``DEV_COMPANY_ID`` is used.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from database.supabase_client import get_supabase_client
from rag.ingestion import STORAGE_BUCKET, ingest_document
from rag.search import search_chunks
from rag.text_extraction import UnsupportedDocumentError
from utils.auth import get_current_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ----------------------------------------------------------------


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    content_type: str
    status: str
    created_at: str
    chunk_count: int = 0


class UploadResponse(BaseModel):
    document_id: UUID
    chunk_count: int
    status: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    similarity: float


class SearchResponse(BaseModel):
    hits: list[SearchHit]


# --- Endpoints --------------------------------------------------------------


@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    company_id: UUID = Depends(get_current_company_id),
) -> UploadResponse:
    """Upload a document and run the full ingestion pipeline synchronously."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename"
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file"
        )

    try:
        result = await ingest_document(
            company_id=company_id,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            data=data,
        )
    except UnsupportedDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc

    return UploadResponse(
        document_id=result.document_id,
        chunk_count=result.chunk_count,
        status=result.status.value,
    )


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    company_id: UUID = Depends(get_current_company_id),
) -> list[DocumentOut]:
    """List all documents belonging to the current company."""
    supabase = get_supabase_client()

    response = (
        supabase.table("documents_with_counts")
        .select("id, filename, content_type, status, created_at, chunk_count")
        .eq("company_id", str(company_id))
        .order("created_at", desc=True)
        .execute()
    )
    return [DocumentOut(**row) for row in (response.data or [])]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    company_id: UUID = Depends(get_current_company_id),
) -> None:
    """Delete a document, its chunks and its storage object."""
    supabase = get_supabase_client()

    doc = (
        supabase.table("documents")
        .select("storage_path, company_id")
        .eq("id", str(document_id))
        .limit(1)
        .execute()
    )
    rows = doc.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if rows[0]["company_id"] != str(company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    storage_path = rows[0]["storage_path"]
    try:
        supabase.storage.from_(STORAGE_BUCKET).remove([storage_path])
    except Exception:
        logger.exception("Failed to remove storage object %s", storage_path)

    supabase.table("documents").delete().eq("id", str(document_id)).execute()


@router.post("/rag/search", response_model=SearchResponse)
async def rag_search(
    body: SearchRequest,
    company_id: UUID = Depends(get_current_company_id),
) -> SearchResponse:
    """Semantic search over the current company's knowledge base."""
    results = await search_chunks(
        query=body.query, company_id=company_id, top_k=body.top_k
    )
    return SearchResponse(
        hits=[
            SearchHit(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                chunk_index=r.chunk_index,
                content=r.content,
                similarity=r.similarity,
            )
            for r in results
        ]
    )
