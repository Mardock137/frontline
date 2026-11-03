-- Migration 016: fix Security Advisor warning "role mutable search_path"
-- Both functions relied on the caller's search_path to resolve object names.
-- Pinning search_path prevents a malicious search_path from redirecting
-- name resolution to attacker-controlled objects.

alter function frontline.set_updated_at() set search_path = frontline, pg_temp;

-- extensions is kept in the search_path so the vector similarity operator
-- (<=>), which lives in the vector extension, still resolves (phase 2).
alter function frontline.match_document_chunks(extensions.vector, uuid, integer) set search_path = frontline, extensions, pg_temp;
