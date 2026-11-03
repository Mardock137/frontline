-- Migration 010: document_chunks
-- Stores the chunked text and embeddings used for semantic search (RAG).
-- One row per chunk; a document typically produces many chunks.
--
-- company_id is denormalized here so the search function can filter by
-- tenant without joining back to documents (faster, plus keeps a single
-- column for future RLS policies).

create table if not exists frontline.document_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references frontline.documents (id) on delete cascade,
    company_id uuid not null references frontline.companies (id) on delete cascade,
    chunk_index integer not null,
    content text not null,
    embedding extensions.vector(1024) not null,
    created_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create index if not exists document_chunks_document_id_idx
    on frontline.document_chunks (document_id);
create index if not exists document_chunks_company_id_idx
    on frontline.document_chunks (company_id);

-- HNSW index on the embedding vector for fast cosine-similarity search.
create index if not exists document_chunks_embedding_idx
    on frontline.document_chunks
    using hnsw (embedding extensions.vector_cosine_ops);

alter table frontline.document_chunks enable row level security;
