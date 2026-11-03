# Supabase database

How to apply Frontline's Supabase migrations, how the tables are structured, and who is allowed to read them.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [🚀 Quick start: applying migrations](#-quick-start-applying-migrations)
- [⚙️ How it works](#️-how-it-works)
- [🔒 Security](#-security)
- [🧪 Testing](#-testing)
- [🔍 Troubleshooting](#-troubleshooting)
- [📚 References](#-references)

---

## 📄 Overview

The database runs on **Supabase** (managed PostgreSQL). The schema is a set of versioned SQL files in [backend/database/migrations/](../backend/database/migrations/). In the MVP, migrations are applied **by hand** from the Supabase SQL Editor.

Every Frontline object (tables, functions, views) lives in a dedicated **`frontline`** schema, so the `public` schema stays free for a possible second product later. The backend selects this schema through the `SUPABASE_SCHEMA` variable (default `frontline`). The `vector` extension (pgvector) lives in a second dedicated schema, **`extensions`**, which leaves `public` completely empty. File storage is separate: it uses the `storage` schema.

The backend connects with the **service role key** (a private key), which bypasses Row Level Security. Customer companies stay isolated because application code always filters on `company_id`.

---

## 🚀 Quick start: applying migrations

The **first time**, and again whenever a new migration is added:

1. Open the Supabase project in the browser.
2. Go to **SQL Editor** → **New query**.
3. Open the files in [backend/database/migrations/](../backend/database/migrations/) **in numeric order** (001, 002, 003, ...).
4. For each file: copy the whole contents, paste them into the SQL Editor, and click **Run**.
5. Check that there are no errors before moving on to the next file.

> ⚠️ Order matters: `002_companies.sql` has to exist before `004_agent_configs.sql` (which has a foreign key to `companies`), and so on.

Afterward, check the result in **Table Editor** (select the `frontline` schema from the dropdown at the top).

> ⚠️ **Exposed schemas**: after creating the `frontline` schema, go to **Settings → API → Exposed schemas** and add `frontline` to the list (next to `public` and `graphql_public`). Save. PostgREST reloads the schema. Without this step the backend cannot read or write the tables.

---

## ⚙️ How it works

### Schema

Every Frontline object lives in the **`frontline`** schema: the tables, the `match_document_chunks` function, the `set_updated_at` trigger function, and the `documents_with_counts` view. The `vector` extension lives in the **`extensions`** schema. The `public` schema stays completely empty, ready for a possible second product later. The backend knows which schema to use through `SUPABASE_SCHEMA` (see [config.md](config.md#-environment-variables)). Do not add `extensions` to Exposed schemas: the backend never queries it directly. The vector operator is used only inside `match_document_chunks`, which lives in `frontline`.

Unlike `public`, a custom schema such as `frontline` gets no default Postgres privileges. [020_grant_frontline_privileges.sql](../backend/database/migrations/020_grant_frontline_privileges.sql) explicitly grants `service_role` privileges on the schema, tables, sequences, and functions, including objects created by later migrations, through `alter default privileges`.

### Tables

| Table             | Description                                                              |
|-------------------|--------------------------------------------------------------------------|
| `companies`       | Customer companies (tenants). Unique `slug` for the public chat URL.     |
| `agent_configs`   | Per-company agent configuration (name, logo, color, tone, language).     |
| `documents`       | Document metadata, plus a reference to Storage.                          |
| `document_chunks` | Text chunks with a `vector(1024)` embedding for semantic search (RAG).   |
| `conversations`   | Live chat conversations.                                                 |
| `messages`        | Conversation messages (`customer` / `agent` / `system`).                 |
| `tickets`         | Tickets the agent opens for cases it cannot resolve, or for escalations. |

### Extensions

- `vector` (pgvector) — installed in the `extensions` schema and used by `document_chunks` for semantic search (HNSW index, cosine distance).
- `pgcrypto` — provides `gen_random_uuid()` for primary keys.

### SQL functions

- `match_document_chunks(query_embedding, match_company_id, match_count)` — returns the top-K chunks most similar to the query for the given company (cosine similarity). Defined in [012_search_function.sql](../backend/database/migrations/012_search_function.sql).

### Storage

A **private** `documents` bucket, created by [009_storage.sql](../backend/database/migrations/009_storage.sql). Files are stored at `<company_id>/<document_id>/<filename>`, which separates tenants and avoids collisions between files that share a name.

### Diagram

See the ER diagram in [architecture.md](architecture.md#️-database-schema).

---

## 🔒 Security

- **Row Level Security** is enabled on every application table.
- **No policies for `anon` or `authenticated`** in the MVP, so the frontend does **not** talk to the database directly. Everything goes through the backend.
- **Service role key**: used only by the backend (`backend/.env`). Never expose it to the frontend, commit it, or paste it into a chat.
- **Application isolation**: every backend query filters on `company_id` (from the session token; locally, from `DEV_COMPANY_ID` only when `ALLOW_DEV_COMPANY_FALLBACK=true`).

---

## 🧪 Testing

Tests for the Pydantic models and the Supabase client:

```bash
cd backend
pytest tests/database -v
```

The tests do **not** touch the real database. Models are validated locally, and the client is tested by patching settings with `monkeypatch`.

---

## 🔍 Troubleshooting

### `extension "vector" is not available`

**Cause**: the pgvector extension is not enabled on the Supabase project.
**Fix**: in Supabase, go to **Database → Extensions** and enable `vector`, or run `001_enable_extensions.sql` from the SQL Editor. On current projects, `create extension if not exists` is enough.

### `RuntimeError: Supabase is not configured`

**Cause**: `SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` is empty in `backend/.env`.
**Fix**: copy the values from the Supabase dashboard (**Project Settings → API**) into `backend/.env`, then restart the process.

### The backend cannot find the tables (`relation ... does not exist`, or a `404` from PostgREST)

**Cause**: the `frontline` schema is not in Supabase's Exposed schemas, or `SUPABASE_SCHEMA` in `backend/.env` is not set to `frontline`.
**Fix**: add `frontline` under **Settings → API → Exposed schemas**, and check that `backend/.env` contains `SUPABASE_SCHEMA=frontline`. Restart the backend.

### `403 Forbidden` / `permission denied for schema frontline` (Postgres `42501`)

**Cause**: `frontline` never received the base privileges for `service_role`. Unlike `public`, a new schema does not grant them automatically. `service_role` bypasses Row Level Security, but not privileges on the schema, tables, views, functions, and sequences.
**Fix**: run [020_grant_frontline_privileges.sql](../backend/database/migrations/020_grant_frontline_privileges.sql) from the Supabase SQL Editor, then restart the backend and reload the dashboard.

### `foreign key violation` while running a migration

**Cause**: the migrations were run out of order.
**Fix**: run them again in numeric order. The `create table if not exists` statements are idempotent, so re-running a file that already applied is safe.

---

## 📚 References

- **SQL migrations**: [backend/database/migrations/](../backend/database/migrations/)
- **Supabase client**: [backend/database/supabase_client.py](../backend/database/supabase_client.py)
- **Pydantic models**: [backend/database/models.py](../backend/database/models.py)
- **Tests**: [backend/tests/database/](../backend/tests/database/)
- **Related docs**: [architecture.md](architecture.md), [config.md](config.md)
- **Supabase docs**: [supabase.com/docs](https://supabase.com/docs)
