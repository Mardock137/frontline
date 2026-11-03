"""Document ingestion pipeline: upload -> extract -> chunk -> embed -> store.

MVP is synchronous: the caller awaits the whole pipeline. For larger
documents this can take a few seconds. A background job queue is
post-MVP.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from database.models import DocumentStatus
from database.supabase_client import get_supabase_client
from integrations.embedding_interfaces.base_embedding_interface import (
    BaseEmbeddingInterface,
)
from integrations.embedding_interfaces.voyage_embedding import get_embedding_client
from rag.chunking import chunk_text
from rag.text_extraction import extract_text

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "documents"


@dataclass
class IngestionResult:
    document_id: UUID
    chunk_count: int
    status: DocumentStatus


async def ingest_document(
    *,
    company_id: UUID,
    filename: str,
    content_type: str,
    data: bytes,
    embedding_client: BaseEmbeddingInterface | None = None,
) -> IngestionResult:
    """Run the full ingestion pipeline for one uploaded file.

    1. Upload the raw file to Supabase Storage (``<company_id>/<filename>``).
    2. Create a ``documents`` row with status ``pending``.
    3. Extract text, chunk it, embed each chunk.
    4. Insert the chunks in ``document_chunks``.
    5. Update the document status to ``ready`` (or ``error``).
    """
    supabase = get_supabase_client()
    embedder = embedding_client or get_embedding_client()

    doc_row = (
        supabase.table("documents")
        .insert(
            {
                "company_id": str(company_id),
                "filename": filename,
                "storage_path": "",
                "content_type": content_type,
                "status": DocumentStatus.PROCESSING.value,
            }
        )
        .execute()
    )
    document_id = UUID(doc_row.data[0]["id"])

    # Unique path per document avoids collisions when two uploads share the
    # same filename (previous behaviour would overwrite the object in Storage
    # and leave one of the rows pointing to someone else's bytes).
    safe_filename = Path(filename).name
    storage_path = f"{company_id}/{document_id}/{safe_filename}"

    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=data,
            file_options={"content-type": content_type},
        )

        supabase.table("documents").update({"storage_path": storage_path}).eq(
            "id", str(document_id)
        ).execute()

        text = extract_text(data, content_type=content_type, filename=filename)
        chunks = chunk_text(text)

        if not chunks:
            _mark_status(supabase, document_id, DocumentStatus.ERROR)
            logger.warning(
                "No text extracted from document %s (%s)", document_id, filename
            )
            return IngestionResult(document_id, 0, DocumentStatus.ERROR)

        embeddings = await embedder.embed(chunks, input_type="document")

        rows = [
            {
                "document_id": str(document_id),
                "company_id": str(company_id),
                "chunk_index": i,
                "content": chunk,
                "embedding": embedding,
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        supabase.table("document_chunks").insert(rows).execute()

        _mark_status(supabase, document_id, DocumentStatus.READY)
        logger.info(
            "Ingested document %s (%s): %d chunks", document_id, filename, len(chunks)
        )
        return IngestionResult(document_id, len(chunks), DocumentStatus.READY)

    except Exception:
        _mark_status(supabase, document_id, DocumentStatus.ERROR)
        logger.exception("Ingestion failed for document %s", document_id)
        raise


def _mark_status(supabase, document_id: UUID, status: DocumentStatus) -> None:
    supabase.table("documents").update({"status": status.value}).eq(
        "id", str(document_id)
    ).execute()
