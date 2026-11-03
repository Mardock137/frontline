-- Migration 019: drop the unused users table.
-- Created in migration 003 in anticipation of multi-user-per-company support,
-- never wired into any endpoint. Whether/how to model per-user access depends
-- on how identity is handled once the external website auth integration lands (see
-- docs/architecture.md - Authentication (SSO from an external site)), so it is removed for
-- now rather than kept unused. Re-add with a fresh design if/when needed.

drop table if exists frontline.users;
