-- Migration 005: documents
-- Knowledge base documents uploaded by each company.
-- The embedding column is reserved for phase 3 (RAG) and stays null for now.

create table if not exists frontline.documents (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references frontline.companies (id) on delete cascade,
    filename text not null,
    storage_path text not null,
    content_type text not null,
    status text not null default 'pending'
        check (status in ('pending', 'processing', 'ready', 'error')),
    embedding extensions.vector(1536),
    created_at timestamptz not null default now()
);

create index if not exists documents_company_id_idx on frontline.documents (company_id);
create index if not exists documents_status_idx on frontline.documents (status);

alter table frontline.documents enable row level security;
