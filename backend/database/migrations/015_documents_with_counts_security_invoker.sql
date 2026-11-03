-- Migration 015: fix Security Advisor error on documents_with_counts
-- By default a view runs with the permissions of its owner (equivalent to
-- SECURITY DEFINER), ignoring the RLS policies and privileges of the caller.
-- Setting security_invoker = true makes the view respect the RLS policies
-- and permissions of the querying user instead.

alter view frontline.documents_with_counts set (security_invoker = true);
