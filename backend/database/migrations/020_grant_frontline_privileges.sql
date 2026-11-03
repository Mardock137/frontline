-- Migration 020: grant missing privileges on the "frontline" schema to
-- service_role. Custom schemas (unlike "public") get no default grants from
-- Postgres, so every REST call from the backend was failing with
-- "permission denied for schema frontline" (Postgres 42501) even though
-- service_role bypasses Row Level Security.

grant usage on schema frontline to service_role;
grant all on all tables in schema frontline to service_role;
grant all on all sequences in schema frontline to service_role;
grant execute on all functions in schema frontline to service_role;

-- Ensure objects created by future migrations get the same grants
-- automatically, without needing another migration like this one.
alter default privileges in schema frontline
    grant all on tables to service_role;
alter default privileges in schema frontline
    grant all on sequences to service_role;
alter default privileges in schema frontline
    grant execute on functions to service_role;
