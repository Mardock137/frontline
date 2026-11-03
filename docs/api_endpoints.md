# API endpoints

HTTP endpoints exposed by the FastAPI backend.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [⭐ Endpoints](#-endpoints)
- [📚 References](#-references)

---

## 📄 Overview

The backend exposes a REST API. The dashboard browser talks to Next.js at `/api/...` for documents and dashboard calls. The proxy adds an `Authorization: Bearer` header taken from the `httpOnly` cookie, and the backend identifies the company from that header. Without a Bearer token the response is `401`, except in local development when `ALLOW_DEV_COMPANY_FALLBACK=true`, in which case `DEV_COMPANY_ID` is used. The proxy returns `403` with an empty body for `POST`, `PATCH`, and `DELETE` requests whose origin does not match the site host. The live chat stays public and calls the backend directly, identified by the slug in the URL. Every backend response is JSON.

---

## ⭐ Endpoints

### `GET /health`

Health check. Returns `{"status": "ok"}`.

### `POST /documents/upload`

Uploads a file and ingests it synchronously into the knowledge base (text extraction, then chunking, embedding, and storage).

- **Body**: `multipart/form-data`, field `file`
- **Supported formats**: PDF, DOCX, TXT, Markdown
- **`201` response**:

```json
{
    "document_id": "uuid",
    "chunk_count": 12,
    "status": "ready"
}
```

- **Auth**: `Authorization: Bearer <session_token>` header. Without a Bearer token the response is `401`, except when `ALLOW_DEV_COMPANY_FALLBACK=true` in local development. From the dashboard, the Next.js proxy adds the Bearer token. The proxy returns `403` if the request origin does not match the site host.
- **Vercel limit**: the dashboard uploads the file through the proxy. On Vercel, a file larger than 4.5 MB is rejected with `413` before it reaches the backend.
- **Errors**: `400` empty file or missing filename, `415` unsupported format, `401` missing or invalid session.

### `GET /documents`

Lists documents for the current company, newest first.

- **`200` response**: array of `{ id, filename, content_type, status, created_at }`.
- **Errors**: `401` missing or invalid session.

### `DELETE /documents/{document_id}`

Deletes the document, its chunks, and the file in Supabase Storage.

- **`204`** on success, `404` if the document does not belong to the company.
- **Errors**: `401` missing or invalid session. From the Next.js proxy, `403` if the origin does not match the site host.

### `POST /rag/search`

Semantic search over the current company's knowledge-base chunks.

- **Body**:

```json
{
    "query": "How do I reset my password?",
    "top_k": 5
}
```

- **`200` response**:

```json
{
    "hits": [
        {
            "chunk_id": "uuid",
            "document_id": "uuid",
            "chunk_index": 2,
            "content": "...",
            "similarity": 0.87
        }
    ]
}
```

- `similarity` is in `[0, 1]` (cosine similarity; higher means more relevant).
- **Errors**: `401` missing or invalid session.

### `POST /auth/sso`

Exchanges the external site's JWT for an internal Frontline session token (24 hours). The site token is single-use.

- **Body**: `{ "sso_token": "..." }`
- The JWT must include `jti` and a `product` claim equal to `support-saas`, along with a valid signature, issuer, audience, and expiry.
- **`200` response**: `{ "session_token": "..." }`
- **Errors**: `401` if the token is expired, invalid, missing the required claims, or already used; `503` if Redis does not respond or `KV_REST_API_URL` / `KV_REST_API_TOKEN` are missing (no session token is issued); `422` empty body.

### `GET /chat/{company_slug}/config`

Returns branding and the welcome message for the live chat page. Public endpoint: no authentication.

- **Path param**: `company_slug` — the company's slug (for example, `acme`).
- **`200` response**:

```json
{
    "agent_name": "Sofia",
    "company_display_name": "Acme Inc.",
    "logo_url": null,
    "primary_color": "#FF5733",
    "welcome_message": "Hi! How can I help?"
}
```

- **Errors**: `404` company or agent config not found.

### `GET /chat/{company_slug}/conversation/{conversation_id}/messages`

Returns the messages of an existing conversation, in chronological order. Public read-only endpoint (no authentication, no rate limit), used by the live chat to restore history after a refresh.

- **Path params**: `company_slug` — the company's slug; `conversation_id` — the conversation UUID.
- **`200` response**: array of `{ id, role, content }` (`system` messages are omitted; the list is empty when there are no messages).

```json
[
    { "id": "uuid", "role": "customer", "content": "How do I reset my password?" },
    { "id": "uuid", "role": "agent",    "content": "Follow these steps..." }
]
```

- **Errors**: `404` company not found, `404` conversation not found or belonging to another company (`"Conversation not found"`).

### `POST /chat/{company_slug}/message`

Sends a message to the AI chatbot of the company identified by `company_slug`. If `conversation_id` is null, a new conversation is created. The agent searches the knowledge base and can open tickets or escalate to a human on its own.

- **Path param**: `company_slug` — the company's slug (for example, `acme`).
- **Body**:

```json
{
    "conversation_id": "optional-uuid-or-null",
    "content": "How do I reset my password?"
}
```

- **`200` response**:

```json
{
    "conversation_id": "uuid",
    "reply": "To reset your password, follow these steps..."
}
```

- **Errors**: `404` company or agent config not found, `404` when `conversation_id` is set but does not exist or belongs to another company (`"Conversation not found"`), `422` empty content, `429` per-IP rate limit exceeded (set with `CHAT_RATE_LIMIT`, default `20/minute`; behind a trusted reverse proxy set `TRUST_PROXY_HEADERS=true` so the limit uses the real client IP), `500` Anthropic API key not configured.

---

## 🖥️ Dashboard endpoints (`/dashboard`)

Every `/dashboard` endpoint, and also `/documents` and `/rag/search`, uses `get_current_company_id`. Without a Bearer token the response is `401` (`Authentication required`), unless the `ALLOW_DEV_COMPANY_FALLBACK` development flag is on, in which case `DEV_COMPANY_ID` is used. A token that is present but invalid returns `401` (`Invalid or expired session token`). Writes that go through the Next.js proxy (`POST`, `PATCH`, and `DELETE` on documents and dashboard) receive `403` if the origin does not match the site host.

### `GET /dashboard/tickets`

Lists every ticket for the current company, newest first.

- **`200` response**: array of `{ id, conversation_id, subject, description, status, is_escalation, created_at, updated_at }`.
- **Errors**: `401` missing or invalid session.
- `status`: `"open"` | `"in_progress"` | `"closed"`.
- `is_escalation`: `true` when the agent opened the ticket as an escalation.

### `PATCH /dashboard/tickets/{ticket_id}`

Updates a ticket's status.

- **Body**: `{ "status": "open" | "in_progress" | "closed" }`
- **`200` response**: the updated ticket.
- **Errors**: `401` missing or invalid session, `404` if the ticket does not exist or does not belong to the company. From the Next.js proxy, `403` if the origin does not match the site host.

### `GET /dashboard/agent-config`

Reads the agent configuration for the current company.

- **`200` response**:

```json
{
    "agent_name": "Sofia",
    "company_display_name": "Acme Inc.",
    "primary_color": "#FF5733",
    "tone": "formal",
    "default_language": "en",
    "welcome_message": "Hi! How can I help?"
}
```

- **Errors**: `401` missing or invalid session, `404` if the configuration does not exist.

### `PATCH /dashboard/agent-config`

Partially updates the agent configuration. Only fields present in the body are changed.

- **Updatable fields**: `agent_name`, `company_display_name`, `primary_color` (hex `#RRGGBB`), `tone` (`formal`|`informal`), `default_language`, `welcome_message`.
- **`200` response**: the updated configuration.
- **Errors**: `401` missing or invalid session, `422` if the body is empty, `404` if the configuration does not exist. From the Next.js proxy, `403` if the origin does not match the site host.

### `GET /dashboard/stats`

Returns aggregate statistics for the current company.

- **`200` response**:

```json
{
    "total_conversations": 142,
    "tickets_by_status": {
        "open": 5,
        "in_progress": 2,
        "closed": 18
    },
    "escalation_open_count": 3
}
```

- **Errors**: `401` missing or invalid session.

---

## 📚 References

- **Documents router**: [backend/api/documents.py](../backend/api/documents.py)
- **Agent router**: [backend/api/agent.py](../backend/api/agent.py)
- **Auth router**: [backend/api/auth.py](../backend/api/auth.py)
- **Config router**: [backend/api/config.py](../backend/api/config.py)
- **Dashboard router**: [backend/api/dashboard.py](../backend/api/dashboard.py)
- **Session / SSO**: [backend/utils/auth.py](../backend/utils/auth.py)
- **Router registration**: [backend/main.py](../backend/main.py)
- **Related docs**: [rag.md](rag.md), [database.md](database.md), [architecture.md](architecture.md), [frontend.md](frontend.md)
