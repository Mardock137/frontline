# Deploy

How to deploy Frontline to staging: packaging the backend, then hosting it on Google Cloud Run and Vercel.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [⚙️ How it works](#️-how-it-works)
- [🧪 Testing](#-testing)
- [📚 References](#-references)

---

## 📄 Overview

For now the project is deployed **to staging only**, not to production. Two pieces need hosting:

- **Backend** (FastAPI) → packaged with Docker and hosted on **Google Cloud Run**.
- **Frontend** (Next.js) → hosted on **Vercel**.

The database (Supabase) is already a managed service, so it does not need a deploy of its own. This stage reuses the existing Supabase project, the same one used for local development.

There is no custom domain yet. The backend and the frontend use the automatic URLs from Cloud Run (`*.run.app`) and Vercel (`*.vercel.app`).

**Current state**: backend and frontend are both online in staging and wired together. The dashboard and the live chat have been tested end to end.

- **Staging backend URL**: `https://<backend-staging>.run.app`
- **Staging frontend URL**: `https://<frontend-staging>.vercel.app`

---

## ⚙️ How it works

### Packaging the backend

The backend is packed into a Docker image by [backend/Dockerfile](../backend/Dockerfile):

- Base image: `python:3.14-slim`.
- Dependencies (`requirements.txt`) are installed in a layer separate from the application code, so the Docker cache is reused when only the code changes.
- The server (`uvicorn`) listens on the port in the `PORT` environment variable (default `8080`), which is what Cloud Run expects when it routes traffic to the container.
- [backend/.dockerignore](../backend/.dockerignore) keeps unnecessary files out of the build context (virtualenv, tests, logs, secrets, caches).

### Local build and run

From the `backend/` folder:

```bash
docker build -t frontline-backend:test .
```

To run the container locally with the variables from your own `.env`:

```bash
docker run --rm -p 8080:8080 --env-file .env -e PORT=8080 frontline-backend:test
```

Check that the backend responds by opening [http://localhost:8080/health](http://localhost:8080/health). It should return `{"status": "ok"}`.

### Deploying the backend to Google Cloud Run

The Cloud Run service **`frontline-backend-staging`** (region `europe-west1`) is set up for **continuous deploy from GitHub through Cloud Build**:

- **Repository**: `Mardock137/frontline`
- **Branch**: `staging` (expression `^staging$`)
- **Dockerfile**: `/backend/Dockerfile` (the `backend/` folder is also the Docker build context)
- **Access**: public, unauthenticated (the backend has to answer the end customer's browser directly)
- **Scaling**: automatic, minimum `0` instances (no cost when there is no traffic)
- **Billing**: per request

Every push to the `staging` branch makes Cloud Build rebuild the image, and Cloud Run publishes a new revision.

### Secrets and configuration on Cloud Run

Sensitive credentials do not live in a `.env` file on the server. They live in **Google Secret Manager**, under this rule: *credentials are secrets, configuration is an ordinary environment variable*.

**Secrets** (read from Secret Manager; the service account has the `Secret Manager Secret Accessor` role):

- `ANTHROPIC_API_KEY`
- `VOYAGE_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `SSO_SHARED_SECRET`
- `FRONTLINE_SESSION_SECRET`
- `KV_REST_API_TOKEN`

**Plain environment variables** (nothing sensitive: public URLs or behavior settings):

| Variable              | Staging value                                                 |
|-----------------------|---------------------------------------------------------------|
| `SUPABASE_URL`        | Supabase project URL (reused from dev/local)                  |
| `SUPABASE_SCHEMA`     | `frontline`                                                   |
| `FRONTEND_URL`        | `https://<frontend-staging>.vercel.app`                       |
| `CHAT_RATE_LIMIT`     | `20/minute`                                                   |
| `TRUST_PROXY_HEADERS` | `true`                                                        |
| `LOG_LEVEL`           | `INFO`                                                        |
| `KV_REST_API_URL`     | REST URL of Frontline's Upstash database                      |

Do not set `DEV_COMPANY_ID` or `ALLOW_DEV_COMPANY_FALLBACK` in staging or production. Without a session, the APIs return `401`.

> **Note on `TRUST_PROXY_HEADERS`**: locally it stays `false` (the default). On Cloud Run it is set to `true`, which is safe there because Google's infrastructure writes `X-Forwarded-For` in front of the container and an outside client cannot forge it.
> **Warning — an IAM grant for every secret**: creating a secret in Secret Manager does not make it readable by the service. Each secret needs the `Secret Manager Secret Accessor` role granted explicitly (Secret Manager → open the secret → **Permissions** → Grant access) to the service account (for example, `<project-number>-compute@developer.gserviceaccount.com`). Forgetting it on a new secret fails the deploy with `Permission denied on secret: ...`. That happened the first time `SSO_SHARED_SECRET` and `FRONTLINE_SESSION_SECRET` were added.

### Deploying the frontend to Vercel

The Vercel project **`frontline-frontend`** is connected to the same GitHub repository, with **Root Directory** set to `frontend` (Vercel detects Next.js from there).

- **Repository**: `Mardock137/frontline`
- **Staging branch**: `staging`, published as a **Preview Deployment** (not as Vercel's "Production", which stays tied to `main` and free for a real production later).
- **`NEXT_PUBLIC_API_URL`**: points at the Cloud Run backend URL, set for both Vercel's Production and Preview environments (Development is left out; locally it uses `frontend/.env.local`). The public chat, the SSO callback, and the `/api` proxy (documents and dashboard) all use it. The dashboard browser no longer calls Cloud Run directly.
- **`NEXT_PUBLIC_WEBSITE_URL`**: URL of the external site (the return link on `/sso/error`). Leave it empty to hide the link.
- **Document upload**: the file goes through Vercel (`/api/documents/upload`). Above 4.5 MB, Vercel responds `413` and the backend never receives the file.

Every push to `staging` makes Vercel rebuild and republish a Preview Deployment on the same URL.

> **A note on the names**: "Production" and "Preview" are Vercel's names for deployment types. They are not the project's business environments (staging and production). At this stage a Vercel Preview Deployment is our staging environment.

### Connecting the external site (SSO)

The external site must redirect to an address that ends with `/sso/callback`.

> **Warning — the URL must end with `/sso/callback`**, not with the bare domain root. If it points only at `https://<domain>`, the SSO token lands on Frontline's home page, which does not read it, and the automatic sign-in never starts. Frontline shows no error.

See [architecture.md](architecture.md#-authentication-sso-from-an-external-site) for the full token flow.

---

## 🧪 Testing

- `docker build` must finish without errors.
- A container started with `docker run` must respond `200 {"status": "ok"}` on `/health`.
- In staging, the Cloud Run service must respond `200 {"status": "ok"}` on `/health` after each new revision (see the URL in Overview).
- In staging, check the flow end to end by opening `/dashboard` (documents, tickets, config, stats) and `/chat/<slug>` on the frontend, with real data from the Cloud Run backend.

---

## 📚 References

- **Dockerfile**: [backend/Dockerfile](../backend/Dockerfile)
- **Dockerignore**: [backend/.dockerignore](../backend/.dockerignore)
- **Related docs**: [config.md](config.md), [repo_structure.md](repo_structure.md), [architecture.md](architecture.md)
- **External**: [Cloud Run](https://cloud.google.com/run), [Secret Manager](https://cloud.google.com/secret-manager), [Vercel](https://vercel.com/docs)
