# Frontline

[![Backend CI](https://github.com/Mardock137/frontline/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Mardock137/frontline/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/Mardock137/frontline/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Mardock137/frontline/actions/workflows/frontend-ci.yml)

- **Python version**: `3.14.4`
- **Project version**: `0.14.0`

## 📋 Contents

- [📄 Description](#-description)
- [🛠️ Stack](#️-stack)
- [🔐 Environment variables](#-environment-variables)
- [🚀 Quick start](#-quick-start)
- [📚 Documentation](#-documentation)

---

## 📄 Description

Frontline is a multi-tenant AI customer-support SaaS. It handles first-line customer requests on its own, through a dedicated live chat.

The customer company sets the system up from a dashboard, uploading its own documents (FAQs, policies, manuals, price lists). Those documents are the knowledge base the AI agent answers from.

> **The dashboard has no login of its own.** It opens with a JWT signed by an external site, exchanged at `POST /auth/sso` for an internal session.

---

## 🛠️ Stack

| Component     | Technology                              |
|---------------|-----------------------------------------|
| Backend       | Python 3.14 · FastAPI · Pydantic        |
| Database      | Supabase (PostgreSQL + pgvector)        |
| File storage  | Supabase Storage                        |
| LLM           | Anthropic Claude (`claude-sonnet-5`)    |
| Embedding     | Voyage AI (`voyage-3`)                  |
| Frontend      | Next.js 16 · React 19 · Tailwind CSS v4 |
| UI components | shadcn/ui                               |

---

## 🔐 Environment variables

### Backend (`backend/.env`)

| Variable                     | Description                                                                                            |
|------------------------------|--------------------------------------------------------------------------------------------------------|
| `ANTHROPIC_API_KEY`          | Anthropic API key (Claude)                                                                             |
| `VOYAGE_API_KEY`             | Voyage AI API key (embeddings)                                                                         |
| `SUPABASE_URL`               | Supabase project URL                                                                                   |
| `SUPABASE_ANON_KEY`          | Supabase public key                                                                                    |
| `SUPABASE_SERVICE_ROLE_KEY`  | Supabase private key (bypasses RLS)                                                                    |
| `SUPABASE_SCHEMA`            | Database schema that holds Frontline's tables, functions, and views (default: `frontline`)             |
| `ALLOW_DEV_COMPANY_FALLBACK` | When `true`, a request with no session uses `DEV_COMPANY_ID`. Local development only (default `false`) |
| `DEV_COMPANY_ID`             | UUID of the development company, used only when `ALLOW_DEV_COMPANY_FALLBACK` is on                     |
| `SSO_SHARED_SECRET`          | Secret shared with the external site, used to verify the incoming JWT                                  |
| `FRONTLINE_SESSION_SECRET`   | Frontline-only secret that signs the internal session token (24 hours)                                 |
| `KV_REST_API_URL`            | REST URL of Frontline's Upstash database (single-use SSO tokens)                                       |
| `KV_REST_API_TOKEN`          | Private token for the same Upstash database. Without the URL and the token, SSO is rejected            |
| `FRONTEND_URL`               | Allowed CORS origin (`*` in development, the exact URL in production)                                  |
| `CHAT_RATE_LIMIT`            | Per-IP request cap on the chat endpoint (default: `20/minute`)                                         |
| `TRUST_PROXY_HEADERS`        | Reads the IP from `X-Forwarded-For` behind a trusted proxy (default: `false`)                          |
| `LOG_LEVEL`                  | Logging level (default: `INFO`)                                                                        |

### Frontend (`frontend/.env.local`)

| Variable                  | Description                                                        |
|---------------------------|--------------------------------------------------------------------|
| `NEXT_PUBLIC_API_URL`     | Base URL of the FastAPI backend (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_WEBSITE_URL` | Optional URL of the external site, used for the return link        |

---

## 🚀 Quick start

### Backend

Run every command from the `backend/` folder.

1. Create the virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate it:

   - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
   - macOS / Linux: `source .venv/bin/activate`

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in the real API keys.

5. Start the development server:

   ```bash
   uvicorn main:app --reload
   ```

6. Check that the server responds by opening [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

To run the test suite (still from `backend/`):

```bash
pytest
```

### Frontend

Run every command from the `frontend/` folder.

1. Install the dependencies (once):

   ```bash
   npm install
   ```

2. Copy `.env.local.example` to `.env.local` and fill in the values.

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Open in the browser:
   - **Dashboard** (`http://localhost:3000/dashboard`) — admin area for the customer company (documents, tickets, agent configuration)
   - **Live chat** (`http://localhost:3000/chat/[slug]`) — public page where the company's end customers talk to the AI agent

> Start the backend and the frontend together, in two separate terminals.

---

## 📚 Documentation

- [Repository structure](docs/repo_structure.md)
- [Architecture](docs/architecture.md)
- [Configuration](docs/config.md)
- [Logging](docs/observability.md)
- [API endpoints](docs/api_endpoints.md)
- [RAG system](docs/rag.md)
- [Frontend](docs/frontend.md)
- [Deploy](docs/deploy.md)

---

Copyright (c) 2026 Mattia Colato. All rights reserved.
