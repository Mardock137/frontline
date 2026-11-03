-- Migration 011: drop the unused embedding column from documents.
-- Embeddings now live in the document_chunks table (see 010).
-- The column was created in migration 005 but never populated.

alter table frontline.documents drop column if exists embedding;
