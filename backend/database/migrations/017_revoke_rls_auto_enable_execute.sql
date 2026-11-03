-- Migration 017: fix Security Advisor warnings on rls_auto_enable()
-- rls_auto_enable() is a Supabase-managed SECURITY DEFINER function backing
-- an event trigger that auto-enables RLS on newly created tables in public.
-- Being SECURITY DEFINER and living in public, it is auto-exposed as a
-- public RPC endpoint (/rest/v1/rpc/rls_auto_enable). It is only meant to
-- run automatically via the DDL event trigger, never called directly by
-- API clients, so direct execution is revoked for anon and authenticated.
-- The function definition and its event trigger are left untouched.

revoke execute on function public.rls_auto_enable() from anon, authenticated;
