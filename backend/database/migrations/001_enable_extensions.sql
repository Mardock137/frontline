-- Migration 001: Enable required PostgreSQL extensions.
-- pgvector is used in phase 3 for semantic search on the knowledge base.

-- Dedicated schema for the vector extension, so it does not live in public
-- (phase 2: closes the Security Advisor warning about extensions in public).
create schema if not exists extensions;
create extension if not exists "vector" with schema extensions;
create extension if not exists "pgcrypto";

-- Dedicated schema for all Frontline objects, so the public schema stays
-- free for a future second product.
create schema if not exists frontline;
