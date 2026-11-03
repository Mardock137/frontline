<!-- markdownlint-disable -->
# 📋 Changelog

## 0.14.0 — 2026-10-15

### Changed

- **`DEV_COMPANY_ID` fallback off by default** (`backend/utils/config.py`, `backend/utils/auth.py`, `backend/.env.example`): without `Authorization: Bearer`, the APIs return `401`. Locally, set `ALLOW_DEV_COMPANY_FALLBACK=true` in `.env`. Do not set the flag or `DEV_COMPANY_ID` in staging or production.
- **Origin check on the proxy** (`frontend/app/api/[...path]/route.ts`): `POST`, `PATCH`, and `DELETE` return `403` when the origin does not match the request host (`Origin`, or `Sec-Fetch-Site: same-origin` when `Origin` is missing). `GET` is unchanged.
- `docs/config.md`, `docs/deploy.md`, `docs/api_endpoints.md`, `docs/architecture.md`, `docs/frontend.md`, `docs/database.md`, `docs/rag.md`, `docs/repo_structure.md`, and `README.md` (version `0.14.0`).

---

## 0.13.1 — 2026-10-09

### Changed

- **Session cookie no longer readable by JavaScript** (`frontend/app/sso/callback/route.ts`, `frontend/lib/session.ts`): `frontline_session` is `httpOnly`. The browser can no longer read the token and does not attach `Authorization: Bearer`.
- **Next.js proxy** (`frontend/app/api/[...path]/route.ts`, `frontend/lib/api.ts`): documents and the dashboard call `/api/...` on the same site. The proxy reads the cookie and adds the Bearer toward the backend. Paths other than `documents` and `dashboard` (chat, auth, rag, health) return `404`. The public chat stays on the backend, without the cookie.
- **Upload on Vercel**: the file goes through the proxy. Above 4.5 MB Vercel returns `413`.
- `docs/architecture.md`, `docs/frontend.md`, `docs/repo_structure.md`, `docs/api_endpoints.md`, `docs/deploy.md`, and `README.md`.
- `README.md`: version bumped to `0.13.1`.

---

## 0.13.0 — 2026-10-08

### Added

- **Single-use SSO token** (`backend/utils/replay_guard.py`, `backend/api/auth.py`): after the signature check, Frontline requires `jti` and `product` equal to `support-saas`. The `jti` is stored on Upstash Redis (`SET` with `NX`, 90-second expiry). A second use of the same token returns `401`. If Redis does not respond, times out, or `KV_REST_API_URL` / `KV_REST_API_TOKEN` are missing, the response is `503` and no session token is issued.

### Changed

- `verify_site_token` returns the company id together with the `jti`. Tokens without `jti` or without the correct `product` are now rejected.
- `docs/config.md`, `docs/api_endpoints.md`, `docs/architecture.md`, `docs/deploy.md`, `docs/repo_structure.md`, `docs/observability.md`, and `README.md`.
- `README.md`: version bumped to `0.13.0`.

---

## 0.12.1 — 2026-09-19

### Fixed

- **GitHub security alert on the frontend** (`frontend/package.json`, `frontend/package-lock.json`): three npm dependencies were on the versions flagged by Dependabot. No change to application code (chat, dashboard, SSO, `next.config.ts`). `npm run lint` and `npm run build` pass on the new stack. Backend and CI workflows unchanged; Dependabot version-update stays disabled (as of 0.8.2).
  - **`next` and `eslint-config-next` from `16.2.12` to `16.3.4`**: closes CVE-2026-75604 / GHSA-p293-qw3h-jr36 (RCE on Next servers hosted on Windows) and GHSA-2xp9-vwfh-vxw4 (RCE in AVIF image optimization via `sharp`/libheif). The advisory lists `16.3.3` as the first patch; `16.3.4` is used because it re-enables AVIF optimization after the upstream fix and fixes a build error with TypeScript 6 (already in use in the project, `6.0.3`). The 16.3 additions (Cache Components, Instant Navigations, Partial Prefetching) stay off: they are opt-in. Staging is on Vercel (Linux), so the Windows CVE was not exploitable in deploy; the jump still closes the alert and covers local development on Windows.
  - **`sharp` override from `^0.35.0` (`0.35.3` resolved) to `0.35.4`**: GHSA-rgj7-g3m4-5g8c, RCE in libheif on Linux if AVIF/HEIF are processed. `sharp` is not imported by the code: Next uses it for `/_next/image` (logo in `frontend/app/chat/[slug]/page.tsx`). The `^0.35.0` range had left the lock on the still-vulnerable `0.35.3`; exact pin so the problem does not happen again.
  - **`js-yaml` override from `4.3.1` to `4.3.2`**: CVE-2026-84375, CPU consumption when parsing untrusted YAML. Transitive dependency of ESLint only (`@eslint/eslintrc`), not present at runtime. The lint config is `frontend/eslint.config.mjs` (JavaScript), not YAML.

---

## 0.12.0 — 2026-08-22

### Added

- **SSO from an external site** (`backend/utils/auth.py`, `backend/api/auth.py`): the site sends a signed JWT (`sso_token` in the query). The backend checks the signature, expiry (10s leeway), issuer `partner-website`, and audience `support-saas`, then issues an internal session token (24h) signed with a different secret, never shared with the site. Endpoint `POST /auth/sso` → `{ session_token }`. A missing, expired, or invalid token → `401`.
- **Real company identity on the dashboard and document APIs**: `get_current_company_id` reads `Authorization: Bearer`. If the header is missing, the fallback to `DEV_COMPANY_ID` remains (local development and existing tests).
- **Frontend callback** (`frontend/app/sso/callback/route.ts`): exchanges the site token, stores the session in a browser-readable cookie (`frontline_session`), redirects to `/dashboard`. Error page `frontend/app/sso/error/page.tsx` with a link back to the site.
- **Authenticated dashboard and document calls** (`frontend/lib/api.ts`): attach `Authorization: Bearer` when the cookie is present. The public live chat is unchanged.
- **Variables** `SSO_SHARED_SECRET` and `FRONTLINE_SESSION_SECRET` in Settings / `.env.example`; dependency `PyJWT`. Frontend: `NEXT_PUBLIC_WEBSITE_URL` for the return link.
- **Test company in staging** in the `frontline` schema, with one `agent_configs` row, used for the SSO end-to-end test.

### Fixed

- **Real end-to-end SSO test in staging**: fixed two configuration problems that showed up during the first trial with a real click from the external site (no code change). The callback URL configured on the external site pointed at the domain root instead of `/sso/callback`, so Frontline never read the token. On the backend, the secrets `SSO_SHARED_SECRET` and `FRONTLINE_SESSION_SECRET` had been created in Secret Manager but without the `Secret Manager Secret Accessor` role granted to the service's service account, causing `Permission denied` on deploy.

### Changed

- `_current_company_id()` duplicated in `dashboard.py` and `documents.py` replaced by the shared dependency.

---

## 0.11.3 — 2026-07-26

### Added

- **Dockerfile for the backend** (`backend/Dockerfile`, `backend/.dockerignore`): image based on `python:3.14-slim`, intended for deploy on Google Cloud Run. The port is read from the `PORT` environment variable (default `8080`), consistent with Cloud Run's behavior. Build and run tested locally: the container responds correctly on `/health`.
- **Documentation updated**: `docs/repo_structure.md` (rows for `Dockerfile` and `.dockerignore`), `docs/deploy.md` (first staging deploy guide, local image build/run section).
- **No impact on app behavior**: no Python code changes, only the containerization infrastructure was added.

---

## 0.11.2 — 2026-07-24

### Fixed

- **Secrets exposed in the log at `LOG_LEVEL=DEBUG`** (`backend/utils/logging_config.py`): at `DEBUG`, the `httpx`, `httpcore`, and `hpack` libraries print the raw HTTP headers of every request, including `Authorization` and `apikey` — that is, the `SUPABASE_SERVICE_ROLE_KEY` in clear text in `backend/logs/backend.log`. `setup_logging()` now forces these three loggers to `WARNING` regardless of the application `LOG_LEVEL`, so debugging business logic no longer risks writing secrets to disk. Application code (every `logger.*` call in the project modules) never logged secrets: the problem was only the third-party HTTP dependencies.
- **Test added** (`backend/tests/utils/test_logging_config.py`): checks that `httpx`/`httpcore`/`hpack` stay at `WARNING` even when the application logger is set to `DEBUG`.
- **Documentation updated**: `docs/observability.md` (new section "Third-party libraries kept quiet").

---

## 0.11.1 — 2026-07-24

### Fixed

- **`403 Forbidden` / `permission denied for schema frontline` (Postgres `42501`) on every REST call to the `frontline` schema** (`backend/database/migrations/020_grant_frontline_privileges.sql`): unlike `public`, a custom schema does not receive default privileges from Postgres, so `service_role` (used by the backend) could not access tables, views, functions, and sequences even though it bypasses Row Level Security. The new migration explicitly grants `usage` on the schema and the privileges on every existing object to `service_role`, plus `alter default privileges` so the same privileges apply automatically to objects created by later migrations.
- **Documentation updated**: `docs/database.md` (section "How it works" and a new Troubleshooting entry), `docs/repo_structure.md` (row for `020_grant_frontline_privileges.sql`).

---

## 0.11.0 — 2026-07-24

### Changed

- **LLM model updated to Claude Sonnet 5** (`backend/config/llm_models/support_agent.yaml`): `model` changes from `claude-sonnet-4-6` to `claude-sonnet-5`, a drop-in replacement according to the Anthropic documentation (same tools, same request/response format). The code does not use `temperature`/`top_p`/`top_k` or manual thinking (`budget_tokens`), so none of the API breaking changes introduced by Sonnet 5 affect the project.
- **`max_tokens` raised from `2048` to `4096`** (same file): on Sonnet 5 adaptive thinking is on by default and consumes part of the same `max_tokens` budget shared with the final reply; the model's new tokenizer also produces about 30% more tokens for the same text. The wider margin prevents truncated replies (`stop_reason: "max_tokens"`). `effort: low` stays unchanged, already the right choice for high-volume customer support.
- **No Python code changes**: `loader.py` and `anthropic_interface.py` read `model`/`max_tokens` dynamically from the YAML without validating the model name.
- **Documentation updated**: `README.md`, `docs/architecture.md`, `docs/config.md` (`claude-sonnet-4-6` references replaced).
- **No impact on real environments**: the project had not yet been deployed to staging or production.

---

## 0.10.2 — 2026-07-22

### Removed

- **`users` table removed** (`backend/database/migrations/019_drop_users_table.sql`): it was not referenced by any endpoint, tool, or agent, only by the Pydantic models (`UserCreate`/`User` in `backend/database/models.py`) and their tests. It had been created in migration `003` in anticipation of future multi-user-per-company support, and was never wired to the rest of the code. As already done for `011_drop_documents_embedding.sql`, the removal is a new numbered migration instead of editing `003` retroactively, which stays as a historical document. No impact on app behavior.

---

## 0.10.1 — 2026-07-22

### Changed

- **`vector` extension moved from the `public` schema to a dedicated `extensions` schema** (migrations `001`, `005`, `010`, `012`, `016`): closes the last Security Advisor warning (`extension vector installed in public`), leaving `public` completely empty. Migration `001_enable_extensions.sql` creates the `extensions` schema and installs `vector` inside it (`with schema extensions`); the type is now explicitly qualified as `extensions.vector` on the legacy `documents.embedding` column (migration `005`), on the `document_chunks.embedding` column and its HNSW index (migration `010`, `extensions.vector_cosine_ops`), and on the `query_embedding` parameter of `match_document_chunks` (migration `012`). The function `search_path` (migration `016`) changes from `frontline, public, pg_temp` to `frontline, extensions, pg_temp` so the `<=>` operator still resolves.
- **No Python code changes and no change to `SUPABASE_SCHEMA`**: no backend module references the `vector` type or its schema; ingestion passes embeddings as lists and search goes through the `match_document_chunks` RPC. The `extensions` schema must not be added to Supabase "Exposed schemas": the backend never queries it directly.

---

## 0.10.0 — 2026-07-21

### Changed

- **All database objects moved into the dedicated `frontline` schema** (migrations `001`-`016`): tables, indexes, triggers, the `set_updated_at` trigger function, the `match_document_chunks` function, and the `documents_with_counts` view now live in the `frontline` schema instead of `public`, so `public` stays free for a future second product. The `vector` extension (pgvector) stays in `public` for now (move postponed to Phase 2). Migration `001_enable_extensions.sql` creates the schema; migrations `002`-`008`, `010`, `011`, `012`, `013`, `014`, `015`, `016` were updated to create or alter objects in `frontline`. The `search_path` of `match_document_chunks` is `frontline, public, pg_temp` so the vector operator `<=>` still resolves (still in `public`). Migrations `009` (storage) and `017`/`018` (the `rls_auto_enable` function managed by Supabase in `public`) stay unchanged.
- **New variable `SUPABASE_SCHEMA`** (`backend/utils/config.py`, `backend/.env.example`): default `frontline`. The Supabase client (`backend/database/supabase_client.py`) passes it through `ClientOptions(schema=...)`, so every existing `.table(...)` and `.rpc(...)` call points at the correct schema with no other code changes.

---

## 0.9.6 — 2026-07-17

### Fixed

- **Security Advisor warning on `rls_auto_enable()`** (`backend/database/migrations/017_revoke_rls_auto_enable_execute.sql`, `backend/database/migrations/018_revoke_rls_auto_enable_execute_public.sql`): the function (created by Supabase to auto-enable RLS on new tables, not by the project code) is `SECURITY DEFINER` and lived in `public`, so it was auto-exposed as a public RPC (`/rest/v1/rpc/rls_auto_enable`) callable by `anon` and `authenticated`. The first revoke (017) removed the privilege directly from `anon`/`authenticated`, but with no effect: those roles inherited it from the privilege granted by default to the `PUBLIC` role (standard Postgres behavior when a function is created). The second migration (018) revokes the privilege directly from `PUBLIC`, removing it at the root for every role that inherits it. The function and its event trigger stay unchanged and still run automatically on new `CREATE TABLE` statements.

---

## 0.9.5 — 2026-07-17

### Fixed

- **Security Advisor warning `role mutable search_path`** (`backend/database/migrations/016_fix_functions_search_path.sql`): the functions `set_updated_at()` and `match_document_chunks()` did not have a fixed `search_path`, so it was resolved using the caller's search_path (risk of "search_path hijacking"). Set `search_path = public, pg_temp` on both, without changing their logic.

---

## 0.9.4 — 2026-07-15

### Fixed

- **Security Advisor error on `documents_with_counts`** (`backend/database/migrations/015_documents_with_counts_security_invoker.sql`): the view was defined without `security_invoker`, so it ran implicitly with the creator's privileges (equivalent to `SECURITY DEFINER`) instead of the querying user's, bypassing RLS on the underlying tables. Set `security_invoker = true` on the view.

---

## 0.9.3 — 2026-06-17

### Fixed

- **Unstable test on the `PATCH /dashboard/agent-config` endpoint** (`backend/api/dashboard.py`): the empty-body check (`422 No fields to update`) ran *after* the Supabase client was created. In CI, where the Supabase keys are not configured, `get_supabase_client()` raised `RuntimeError` before the check, failing `test_update_agent_config_empty_body` (expected `422`, got `500`). Locally the test passed because the `.env` with the real keys hid the problem. The empty-body check was moved before client creation: with an empty body the endpoint returns `422` immediately without contacting the database.

### Changed

- **CI on direct pushes too** (`.github/workflows/backend-ci.yml`, `.github/workflows/frontend-ci.yml`): added the `push` trigger next to `pull_request` (same `paths` filter). Previously tests ran only when a Pull Request was opened, so direct pushes were never checked. The suite now runs on both pushes and PRs, on every branch.

---

## 0.9.2 — 2026-06-17

### Fixed

- **Lint error `react-hooks/set-state-in-effect`** (`frontend/app/dashboard/documents/page.tsx`): the Documents page loaded the initial data by calling an `async` function (`void fetchDocuments()`) inside `useEffect`, tripping the new React Hooks rule. The `useEffect` now uses the promise-chain style (`getDocuments().then().catch().finally()`), consistent with the other dashboard pages (tickets, config, stats). The `fetchDocuments` function stays unchanged for the refresh after upload. No behavior change.

---

## 0.9.1 — 2026-06-17

### Fixed

- **Frontend linting broken** (`frontend/eslint.config.mjs`, `frontend/package.json`): in Next.js 16 the `next lint` command was removed, causing the `npm run lint` script (and the matching CI step) to fail. Migration to the ESLint CLI standard: created `eslint.config.mjs` with the native flat config (`eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`, already included in the dependencies) and updated the script to `"lint": "eslint ."`. No new dependency, no change to the CI workflow.

---

## 0.9.0 — 2026-06-17

### Added

- **Chat history persistence** (`frontend/app/chat/[slug]/page.tsx`, `frontend/lib/api.ts`): the browser stores the `conversation_id` in localStorage (`support:conversation:<slug>`) after the first message sent. When the page is opened again, the real history is reloaded from the database through the new endpoint and shown in the chat (preceded by the configured welcome message). If the saved id is stale (conversation not found), the localStorage key is cleared and the chat starts over with no visible error.
- **Endpoint `GET /chat/{company_slug}/conversation/{conversation_id}/messages`** (`backend/api/agent.py`): new public read-only endpoint that returns a conversation's messages in chronological order (`system` role excluded). Includes the same cross-tenant check as the POST: anyone who does not know both the slug and the `conversation_id` cannot access the conversation.
- **`ChatMessage` type and `getConversationMessages` function** (`frontend/lib/api.ts`): new type `{ id, role, content }` and fetch function with `AbortSignal` support.
- **Tests** (`backend/tests/api/test_agent.py`): 5 tests for the new endpoint — happy path with messages, empty list, 404 company not found, 404 conversation not found, 404 cross-tenant.

---

## 0.8.5 — 2026-06-17

### Added

- **Rate limiting on the chat endpoint** (`backend/api/agent.py`, `backend/main.py`, `backend/utils/rate_limit.py`): added a cap on requests to `POST /chat/{company_slug}/message` through the `slowapi` library. The count is by IP address, in memory (suitable for the single-instance MVP). Anyone over the limit receives `429 Too Many Requests` without the Claude call running. The limit is configurable from `.env` with the `CHAT_RATE_LIMIT` variable (default `20/minute`).
- **`backend/utils/rate_limit.py`**: single module that exposes the `Limiter` instance shared by `main.py` and `api/agent.py`, avoiding circular imports.
- **`CHAT_RATE_LIMIT`** in `Settings` (`backend/utils/config.py`) and documented in `backend/.env.example`.
- **`slowapi==0.1.10`** added to `backend/requirements.txt`.
- **`429` test** in `backend/tests/api/test_agent.py`: checks that past the limit the endpoint returns `429` and that `SupportAgent.run` is not called.
- **`disable_rate_limiter` fixture** in `backend/tests/conftest.py` (`autouse=True`): disables the limiter for every existing test, which stay unchanged and green.
- **Proxy support in rate limiting** (`backend/utils/rate_limit.py`, `backend/utils/config.py`): new variable `TRUST_PROXY_HEADERS` (default `false`). When on, the IP used as the rate-limiter key is read from the first entry of the `X-Forwarded-For` header instead of the socket. Fixes the case where, behind a reverse proxy or load balancer, every request would arrive with the proxy IP and all visitors would share one counter. The header is considered only with explicit trust: trusting it with no proxy in front would let anyone forge the IP and skip the limit.
- **`TRUST_PROXY_HEADERS`** documented in `backend/.env.example`, `docs/config.md`, `docs/api_endpoints.md`, and the variables table in `README.md`.
- **IP bucketing test** in `backend/tests/api/test_agent.py`: with `TRUST_PROXY_HEADERS=true`, different IPs in `X-Forwarded-For` have separate counters (one IP is blocked with `429` while another gets through).

---

## 0.8.4 — 2026-06-16

### Fixed

- **Supabase queries that do not block the chat path** (`backend/api/agent.py`, `backend/agents/support_agent.py`, `backend/rag/search.py`): every synchronous Supabase call on the live-chat path is now wrapped in `asyncio.to_thread`, matching the pattern already used in `tools/ticket.py` and `tools/escalation.py`. Previously every DB query blocked the whole event loop, so no connected user could receive a reply while one query was waiting. No migration to the `AsyncClient` (out of MVP scope).

---

## 0.8.3 — 2026-06-16

### Accessibility

- **Message live region** (`frontend/components/chat/ChatWindow.tsx`): the message container is now a live region (`role="log"`, `aria-live="polite"`, `aria-relevant="additions"`, `aria-label="Conversation"`). Screen readers announce each new message without interrupting the user.
- **Sender in the bubbles** (`frontend/components/chat/MessageBubble.tsx`): each bubble prepends an `sr-only` label with the sender's name ("Assistant:" / "You:"), invisible on screen but read by screen readers.
- **Perceivable "is typing" indicator** (`frontend/components/chat/TypingIndicator.tsx`): added an `sr-only` text "Assistant is typing" (announced by the live region that contains it) and the three animated dots marked `aria-hidden="true"` (decorative).
- **Input field** (`frontend/components/chat/MessageInput.tsx`): added `aria-label="Type a message"` on the textarea; the `placeholder` alone is not a reliable label for screen readers.
- **Active page in the sidebar** (`frontend/app/dashboard/layout.tsx`): added `aria-label="Main navigation"` on the `nav` and `aria-current="page"` on the active link; the current section is now communicated to screen readers as well as by color.
- **Language consistent for screen readers**: every ARIA / `sr-only` label is in English, aligned with the visible interface text.

---

## 0.8.2 — 2026-06-16

### Removed

- **Dependabot** (`.github/dependabot.yml`): removed the configuration for automatic dependency updates (backend `pip` and frontend `npm`). Version updates are handled by hand. GitHub security alerts (independent of this file) stay unchanged.

---

## 0.8.1 — 2026-06-16

### Fixed

- **Deprecated HTTP 422 constant** (`backend/api/dashboard.py`): replaced `status.HTTP_422_UNPROCESSABLE_ENTITY` with `status.HTTP_422_UNPROCESSABLE_CONTENT` (renamed in Starlette). Same status code `422`, no behavior change; removes the `DeprecationWarning` from the test suite.

---

## 0.8.0 — 2026-06-16

### Added

- **`effort` parameter on `LLMModelConfig`** (`backend/config/llm_models/loader.py`): new optional field with default `"high"` and validation on the allowed values (`low`, `medium`, `high`, `xhigh`, `max`). YAML files that do not define it keep working unchanged.
- **`effort: low` in `support_agent.yaml`** (`backend/config/llm_models/support_agent.yaml`): the effort level is now set explicitly to `low`, consistent with high-volume customer-support use (lower latency and cost).
- **`effort` override in `AnthropicInterface`** (`backend/integrations/llm_interfaces/anthropic_interface.py`): the constructor accepts the optional `effort` parameter; the `chat()` method always passes `output_config={"effort": ...}` to the Anthropic SDK.
- **Tests updated**: added cases in `backend/tests/config/test_llm_models_loader.py` (read from YAML, default `high`, error on an invalid value) and in `backend/tests/integrations/llm_interfaces/test_anthropic_interface.py` (checks `_effort`, override, and `output_config` present on the SDK call).

---

## 0.7.8 — 2026-04-27

### Added

- **Frontend Dependabot** (`.github/dependabot.yml`): added weekly automatic monitoring of npm dependencies in the `frontend/` folder, with update PRs created directly on GitHub.
- **Frontend GitHub Actions CI** (`.github/workflows/frontend-ci.yml`): new workflow that runs on every PR touching the frontend, installs dependencies with `npm ci`, runs `npm run lint`, then `npm run build`.

---

## 0.7.7 — 2026-04-27

### Added

- **Dependabot** (`.github/dependabot.yml`): automatically checks the backend Python dependencies (`/backend`) every week and opens update PRs on the GitHub repo.
- **GitHub Actions CI** (`.github/workflows/backend-ci.yml`): workflow that runs on every PR touching files in `backend/`. Installs the dependencies and runs `pytest` on its own. No secrets required (the tests are fully mocked).

---

## 0.7.6 — 2026-04-27

### Fixed

- **Shared test fixtures** (`backend/tests/conftest.py`, `backend/tests/api/test_agent.py`, `backend/tests/api/test_config.py`, `backend/tests/agents/test_support_agent.py`): centralized the `company_id` and `conversation_id` fixtures in `conftest.py`, removing the local duplicates in the test modules.
- **`BaseAgent` coverage completed** (`backend/tests/agents/test_base_agent.py`): added tests on the abstract class contract, including forbidden instantiation, a valid concrete subclass, and a check of the async `run()` method.
- **Infrastructure errors covered** (`backend/tests/api/test_agent.py`, `backend/tests/api/test_config.py`, `backend/tests/api/test_dashboard.py`): added `500` tests for cases where the agent or Supabase raise unhandled errors.
- **Less brittle agent test** (`backend/tests/agents/test_support_agent.py`): rewrote the unknown-tool test to check the agent's final result instead of depending on the internal structure of `call_args_list`.
- **Suite checked**: the updated tests pass.

## 0.7.5 — 2026-04-27

### Fixed

- **Custom button classes** (`frontend/components/ui/button.tsx`): fixed the `className` merge in the `Button` components, so classes passed by the caller are no longer ignored or dropped silently.
- **Safer toasts** (`frontend/components/ui/toast.tsx`): auto-dismiss timeouts are now tracked and cancelled when `ToastProvider` unmounts, avoiding state updates after unmount. Toast ids also use `crypto.randomUUID()` instead of `Math.random()`.
- **Public chat without a race condition** (`frontend/app/chat/[slug]/page.tsx`, `frontend/lib/api.ts`): the initial config load uses `AbortController` and cleanup in the `useEffect`, so a fast navigation no longer causes `setState` on an already unmounted component.

## 0.7.4 — 2026-04-27

### Fixed

- **Agent tools that do not block** (`backend/tools/ticket.py`, `backend/tools/escalation.py`, `backend/agents/support_agent.py`): `create_ticket` and `escalate` were converted to async functions and now run Supabase calls with `asyncio.to_thread`, avoiding blocking the event loop during FastAPI requests.
- **Reusable Voyage client** (`backend/integrations/embedding_interfaces/voyage_embedding.py`): the HTTP client toward Voyage AI is now created once in the `VoyageEmbedding` instance and reused for every embedding request, avoiding a new connection on each call.
- **Dashboard stats optimized** (`backend/api/dashboard.py`): the ticket count no longer downloads every row into memory. It now uses count queries directly on the database for `open`, `in_progress`, `closed`, and open escalations.
- **Tests updated** (`backend/tests/tools/test_ticket.py`, `backend/tests/tools/test_escalation.py`, `backend/tests/agents/test_support_agent.py`, `backend/tests/api/test_dashboard.py`): aligned with the async tools and the new database-side count strategy. Suite checked with every test passing.

## 0.7.3 — 2026-04-26

### Fixed

- **Document ingestion pipeline** (`backend/rag/ingestion.py`): storage upload and the `storage_path` update were moved inside the `try/except` block, so an error in these steps correctly marks the document as `ERROR` instead of leaving it stuck in `PROCESSING`.
- **Upload filename sanitization** (`backend/rag/ingestion.py`): the storage path now uses `Path(filename).name`, so any directory components are removed from the filename sent by the user.
- **More robust escalation** (`backend/tools/escalation.py`): ticket insert and conversation update are handled separately. If the insert fails, a controlled error is returned; if only the conversation update fails, the problem is logged but the created ticket is not lost.
- **Tests updated**: added targeted cases in `backend/tests/rag/test_ingestion.py` and `backend/tests/tools/test_escalation.py` covering storage failure, filename sanitization, ticket insert failure, and conversation update failure.

## 0.7.2 — 2026-04-26

### Fixed

- **Backend CORS** (`backend/main.py`): fixed the `allow_credentials` configuration when `FRONTEND_URL` is `*`. Previously the backend sent an invalid CORS combination (`*` + credentials enabled), which could make the browser reject the responses.
- **External logos in the chat** (`frontend/next.config.ts`): added `remotePatterns` to allow remote images through `next/image`, required to support company logos hosted on external domains.
- **Crashes in the agent tools** (`backend/agents/support_agent.py`): tool parameters are now read safely with `.get()` instead of crashing if Claude omits a required field. Incomplete cases return a controlled error message instead of a `500`.
- **Tests updated** (`backend/tests/agents/test_support_agent.py`): added 3 tests checking that `search_knowledge`, `create_ticket`, and `escalate` do not crash when they receive incomplete input.

## 0.7.1 — 2026-04-26

### Fixed

- **Chat endpoint security** (`backend/api/agent.py`): added a cross-tenant check on `conversation_id` to prevent reuse of conversations that belong to another company. If the conversation does not belong to the current tenant, the endpoint returns `404`.
- **`AnthropicInterface`** (`backend/integrations/llm_interfaces/anthropic_interface.py`): fixed handling of replies with multiple `text` blocks, which previously overwrote earlier segments. All blocks are now concatenated in the correct order.
- **Tests updated**: added targeted cases in `backend/tests/api/test_agent.py` and `backend/tests/integrations/llm_interfaces/test_anthropic_interface.py` covering both the cross-tenant check and multi-block text replies.

---

## 0.7.0 — 2026-04-26

### Added

- **Company dashboard** (`/dashboard`): admin area for managing documents, tickets, agent configuration, and statistics. Accessible without login (uses `DEV_COMPANY_ID` like the rest of the MVP).
- **Backend `backend/api/dashboard.py`**: 5 new REST endpoints registered on `/dashboard`:
  - `GET /dashboard/tickets` — list of the company's tickets (all of them, ordered by date, with the `is_escalation` field).
  - `PATCH /dashboard/tickets/{ticket_id}` — updates the ticket status (`open` → `in_progress` → `closed`).
  - `GET /dashboard/agent-config` — reads the agent's current configuration.
  - `PATCH /dashboard/agent-config` — partial update: `agent_name`, `company_display_name`, `primary_color`, `tone`, `default_language`, `welcome_message`.
  - `GET /dashboard/stats` — returns total conversations, tickets by status, and the open-escalation count.
- **Tests `backend/tests/api/test_dashboard.py`**: 11 tests with Supabase fully mocked (every endpoint, happy path + 404/422/wrong company errors).
- **UI components** in `frontend/components/ui/`: `button`, `card`, `badge`, `table`, `input`, `label`, `select`, `textarea`, `dialog`, `toast` — built with Tailwind CSS v4 and `class-variance-authority`.
- **`ToastProvider`** + `useToast` hook: contextual notification system (success/error/info) with auto-dismiss after 4 seconds.
- **API functions** added to `frontend/lib/api.ts`: `getDocuments`, `uploadDocument`, `deleteDocument`, `getTickets`, `updateTicketStatus`, `getAgentConfig`, `updateAgentConfig`, `getStats`.
- **Dashboard layout** `frontend/app/dashboard/layout.tsx`: navigation sidebar with links to Documents, Tickets, Configuration, Statistics.
- **Documents page** `frontend/app/dashboard/documents/page.tsx`: upload through a button, file list with status and chunk count, deletion with confirm.
- **Tickets page** `frontend/app/dashboard/tickets/page.tsx`: ticket list with status/escalation badges, status-change buttons, escalation alert banner.
- **Configuration page** `frontend/app/dashboard/config/page.tsx`: full form for `agent_name`, `company_display_name`, `primary_color` (color picker + hex), `tone`, `default_language`, `welcome_message`.
- **Statistics page** `frontend/app/dashboard/stats/page.tsx`: 4 stat cards (conversations, tickets, open escalations, closed tickets) + progress bars by ticket status.
- **Redirect** `frontend/app/dashboard/page.tsx` → `/dashboard/documents`.

### Changed

- `backend/main.py`: registered the new `dashboard_router` with the `/dashboard` prefix.
- `frontend/lib/api.ts`: internal refactor with a `handleResponse<T>` helper to avoid duplicating error handling.

---

## 0.6.0 — 2026-04-24

### Added

- **Public Live Chat page** (`/chat/[slug]`): a company's end customers can open the chat directly in the browser without login. On load, company branding and the welcome message are shown; later messages are handled by the AI agent.
- **Endpoint `GET /chat/{company_slug}/config`**: returns agent name, company name, logo, primary color, and welcome message. No authentication required ([backend/api/config.py](backend/api/config.py)).
- **`CORSMiddleware`** (FastAPI built-in): the backend now accepts cross-origin requests. In development every origin is allowed (`*`); in production it is limited to `FRONTEND_URL` ([backend/main.py](backend/main.py)).
- **`FRONTEND_URL` variable** in `Settings` and in `.env.example` ([backend/utils/config.py](backend/utils/config.py)).
- **Tests `tests/api/test_config.py`**: 4 tests with Supabase mocked (happy path, 404 company, 404 agent_config, logo_url present).
- **Next.js 15 project** in `frontend/` with App Router, TypeScript, Tailwind CSS v4.
- **`frontend/lib/api.ts`**: `getConfig(slug)` and `sendMessage(slug, payload)` functions toward the FastAPI backend.
- **React components** ([frontend/components/chat/](frontend/components/chat/)):
  - `ChatWindow.tsx` — message container with automatic scroll.
  - `MessageBubble.tsx` — message bubble with the primary color for the customer and a neutral style for the agent.
  - `MessageInput.tsx` — textarea with send via Enter or button; dynamic button color.
  - `TypingIndicator.tsx` — three animated dots shown while waiting for the reply.
- **`frontend/.env.local.example`** with `NEXT_PUBLIC_API_URL`.

### Changed

- `backend/main.py`: registered the new `/chat/{slug}/config` router and added `CORSMiddleware`.

---

## 0.5.0 — 2026-04-24

### Added

- **Autonomous AI agent with tool calling** (`SupportAgent`): full loop that calls Claude, runs the requested tools, and saves messages to the DB ([backend/agents/support_agent.py](backend/agents/support_agent.py)).
- **Three tools the agent can call** ([backend/tools/](backend/tools/)):
  - `knowledge.py` — semantic search on the company knowledge base (`search_knowledge`).
  - `ticket.py` — creates a support ticket with `is_escalation=False` (`create_ticket`).
  - `escalation.py` — creates a ticket with `is_escalation=True` and updates the conversation status to `ESCALATED` (`escalate`).
- **`AnthropicInterface`**: concrete adapter for Claude with native tool-calling support ([backend/integrations/llm_interfaces/anthropic_interface.py](backend/integrations/llm_interfaces/anthropic_interface.py)).
- **`BaseLLMInterface` updated**: `generate(prompt)` replaced with `chat(messages, system, tools)`, a better fit for modern models; added `ChatResponse` and `ToolUse` dataclasses ([backend/integrations/llm_interfaces/base_llm_interface.py](backend/integrations/llm_interfaces/base_llm_interface.py)).
- **System prompt template** for the support agent: agent name, company, tone, language, tool instructions ([backend/config/prompts/support_agent.py](backend/config/prompts/support_agent.py)).
- **Endpoint `POST /chat/{company_slug}/message`**: creates a conversation if needed, runs the agent, and returns the reply ([backend/api/agent.py](backend/api/agent.py)).
- **SQL migration 014** ([backend/database/migrations/014_tickets_add_is_escalation.sql](backend/database/migrations/014_tickets_add_is_escalation.sql)): `is_escalation boolean NOT NULL DEFAULT false` column on the `tickets` table.
- **Pydantic models updated**: `TicketCreate` and `Ticket` now expose `is_escalation: bool = False`.
- **`config/llm_models/support_agent.yaml`**: model configuration file for the support agent (`model`, `max_tokens`). Edit this file to change the model or the limits without touching the code.
- **`config/llm_models/loader.py`**: `load_model_config(name)` function and immutable `LLMModelConfig` dataclass. The system is extensible: each agent will have its own YAML identified by name.
- **Full tests with mocks** (no real calls to external services):
  - `backend/tests/tools/test_knowledge.py`
  - `backend/tests/tools/test_ticket.py`
  - `backend/tests/tools/test_escalation.py`
  - `backend/tests/agents/test_support_agent.py`
  - `backend/tests/api/test_agent.py`
  - `backend/tests/integrations/llm_interfaces/test_base_llm_interface.py` (rewritten)
  - `backend/tests/config/test_llm_models_loader.py`
  - `backend/tests/integrations/llm_interfaces/test_anthropic_interface.py`

### Changed

- `BaseLLMInterface.generate` → `BaseLLMInterface.chat` (internal breaking change; no external code depended on it).
- `backend/main.py`: registered the new `/chat` router.
- `AnthropicInterface`: removed the hardcoded `DEFAULT_MODEL`; model and max_tokens are now loaded from `support_agent.yaml` at startup. Both remain overridable by argument for tests and one-off use.
- `get_llm_client()`: accepts `config_name` instead of `model`.

---

## 0.4.0 — 2026-04-21

### Added

- Full RAG system: document upload, text extraction (PDF/DOCX/TXT/Markdown), chunking with overlap, embeddings on Voyage AI (`voyage-3`, 1024 dim), storage in pgvector, and multi-tenant semantic search.
- New `document_chunks` table with an HNSW index on `embedding` ([migration 010](backend/database/migrations/010_document_chunks.sql)).
- SQL function `match_document_chunks` for top-K search filtered by `company_id` ([migration 012](backend/database/migrations/012_search_function.sql)).
- SQL view `documents_with_counts` to expose the chunk count per document ([migration 013](backend/database/migrations/013_documents_with_counts_view.sql)), exposed via `GET /documents` as the `chunk_count` field.
- Storage bucket `documents` managed by the upload endpoint with key `<company_id>/<document_id>/<filename>` to avoid collisions when two uploads share the same filename.
- Automatic batching in `VoyageEmbedding`: requests split into blocks of 128 inputs (Voyage API limit), transparent to callers.
- Abstract interface `BaseEmbeddingInterface` and `VoyageEmbedding` implementation (REST call via `httpx`, for compatibility with Python 3.14).
- `backend/rag/` modules: `text_extraction`, `chunking`, `ingestion`, `search`.
- API endpoints: `POST /documents/upload`, `GET /documents`, `DELETE /documents/{id}`, `POST /rag/search` ([backend/api/documents.py](backend/api/documents.py)).
- New Pydantic models `DocumentChunkCreate` / `DocumentChunk`.
- `VOYAGE_API_KEY` variable in [Settings](backend/utils/config.py) and `.env.example`.
- Dependencies: `pypdf`, `python-docx`, `python-multipart`.
- Tests with full mocks of external services: chunking, extraction, ingestion, search, Voyage client, document/search endpoints.
- New documentation [docs/rag.md](docs/rag.md); updated [architecture](docs/architecture.md), [database](docs/database.md), [api_endpoints](docs/api_endpoints.md), [repo_structure](docs/repo_structure.md).

### Changed

- Removed the `documents.embedding` column ([migration 011](backend/database/migrations/011_drop_documents_embedding.sql)): embeddings now live on `document_chunks`.
- `VoyageEmbedding` HTTP timeout raised from 30s to 60s (default) to support larger chunk batches.

---

## 0.3.0 — 2026-04-21

### Added

- Database schema as versioned SQL migrations in [backend/database/migrations/](backend/database/migrations/): `companies`, `users`, `agent_configs`, `documents` (with an `embedding` column for the future RAG), `conversations`, `messages`, `tickets`.
- PostgreSQL extensions `vector` (pgvector) and `pgcrypto` enabled.
- Private Supabase Storage bucket `documents` for the knowledge base.
- Row Level Security enabled on every application table (the backend uses the service role key and bypasses RLS).
- Cached Supabase client factory ([backend/database/supabase_client.py](backend/database/supabase_client.py)).
- Pydantic models for every table with typed enums ([backend/database/models.py](backend/database/models.py)).
- Model and Supabase client tests ([backend/tests/database/](backend/tests/database/)).
- New documentation: [docs/architecture.md](docs/architecture.md) (schema and architectural choices) and [docs/database.md](docs/database.md) (operational guide to the migrations).

---

## 0.2.0 — 2026-04-20

### Added

- Initial repo structure (`backend/`, `docs/`, `dev_support/`).
- Python backend scaffolding with FastAPI and the `/health` endpoint.
- Configuration system through `pydantic-settings` and a `.env` file ([backend/utils/config.py](backend/utils/config.py)).
- Centralized logging system with console output and a rotating file ([backend/utils/logging_config.py](backend/utils/logging_config.py)).
- Abstract classes `BaseAgent` ([backend/agents/base_agent.py](backend/agents/base_agent.py)) and `BaseLLMInterface` ([backend/integrations/llm_interfaces/base_llm_interface.py](backend/integrations/llm_interfaces/base_llm_interface.py)) as the foundation for agents and LLM integrations.
- `pytest` configuration ([backend/pytest.ini](backend/pytest.ini)) and the initial test suite (health endpoint, settings, logging).
- Starting Python dependencies ([backend/requirements.txt](backend/requirements.txt)).
- Initial documentation: repo structure, configuration, logging system.

---

## 0.1.0 — 2026-04-17

- Initial project setup.
