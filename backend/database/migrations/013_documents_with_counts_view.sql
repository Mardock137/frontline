-- Migration 013: view documents_with_counts
-- Convenience view that exposes every document together with the number of
-- chunks indexed for it. Used by GET /documents in the dashboard to show
-- quickly which documents are fully ingested.

create or replace view frontline.documents_with_counts as
select
    d.id,
    d.company_id,
    d.filename,
    d.storage_path,
    d.content_type,
    d.status,
    d.created_at,
    coalesce(c.chunk_count, 0)::int as chunk_count
from frontline.documents d
left join (
    select document_id, count(*) as chunk_count
    from frontline.document_chunks
    group by document_id
) c on c.document_id = d.id;
