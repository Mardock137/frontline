-- Migration 012: match_document_chunks
-- SQL function used by the RAG search: given a query embedding and a
-- company_id, returns the top-K most similar chunks (cosine similarity).
--
-- Similarity is computed as (1 - cosine_distance), so values are in [0, 1]
-- where 1.0 means identical direction. Ordering is by distance ascending
-- (smaller distance = more similar) for efficiency with the HNSW index.

create or replace function frontline.match_document_chunks(
    query_embedding extensions.vector(1024),
    match_company_id uuid,
    match_count integer default 5
)
returns table (
    id uuid,
    document_id uuid,
    chunk_index integer,
    content text,
    similarity float
)
language sql
stable
as $$
    select
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity
    from frontline.document_chunks dc
    where dc.company_id = match_company_id
    order by dc.embedding <=> query_embedding
    limit match_count;
$$;
