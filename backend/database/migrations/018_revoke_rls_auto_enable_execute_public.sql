-- Migration 018: fix for 017 not clearing the Security Advisor warnings
-- Postgres grants EXECUTE on newly created functions to the PUBLIC
-- pseudo-role by default. anon and authenticated inherit that grant from
-- PUBLIC rather than holding it directly, so revoking from anon/authenticated
-- alone (migration 017) had no effect. Revoking from PUBLIC removes the
-- privilege at its source for every role, anon and authenticated included.

revoke execute on function public.rls_auto_enable() from public;
