-- Migration 009: Supabase Storage bucket for knowledge base documents.
-- The bucket is private: only the backend (service role) can read/write
-- directly. Per-company isolation is enforced by prefixing objects with
-- the company id: "<company_id>/<filename>".

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;

-- RLS on storage.objects is already enabled by Supabase.
-- No anon/authenticated policies are added yet: the service role used by
-- the backend bypasses RLS. Real auth-aware policies will be added when
-- the external website auth integration lands.
