# Configuration

Reference for the backend configuration system: environment variables, the `.env` file, the `Settings` class, and the `config/` folder for static settings.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [⚙️ How it works](#️-how-it-works)
- [🔧 Environment variables](#-environment-variables)
- [🚀 Initial setup](#-initial-setup)
- [📚 References](#-references)

---

## 📄 Overview

Backend configuration falls into two groups:

- **Secret / per environment** (API keys, service URLs, development identity): environment variables loaded from the `.env` file. This file is never committed.
- **Static / non-sensitive** (LLM model settings, system prompts, and so on): files inside `backend/config/`, versioned with the code.

---

## ⚙️ How it works

### Environment variables

Environment variables are loaded from `backend/.env` with [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). The `Settings` class in [backend/utils/config.py](../backend/utils/config.py) exposes each variable as a typed attribute.

Code reads the configuration through `get_settings()`, which returns a singleton cached with `lru_cache`:

```python
from utils.config import get_settings

settings = get_settings()
api_key = settings.ANTHROPIC_API_KEY
```

### The `config/` folder

[backend/config/](../backend/config/) holds static, non-sensitive settings, split into folders by area:

- `llm_models/` — LLM parameters (model name, temperature, max tokens, and so on)
- `prompts/` — system prompts for the AI agent and its tools

Both folders are already populated.

#### LLM model configuration (`llm_models/`)

Each agent has its own YAML file in `backend/config/llm_models/`. The loader (`loader.py`) reads the file, validates the fields, and returns an immutable `LLMModelConfig` dataclass.

Supported fields:

| Field        | Type  | Required | Default | Description                                                                                                                                                                                                                                         |
|--------------|-------|----------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `model`      | `str` | Yes      | —       | Claude model id (for example, `claude-sonnet-5`).                                                                                                                                                                                                   |
| `max_tokens` | `int` | Yes      | —       | Maximum number of tokens the model may generate in one reply.                                                                                                                                                                                       |
| `effort`     | `str` | No       | `high`  | How many tokens Claude spends on the reply (text, tool calls, and any thinking). Thinking does not have to be enabled. Valid values: `low`, `medium`, `high`, `xhigh`, `max`. Lower values reduce latency and cost. `high` matches the API default. |

Example (`support_agent.yaml`):

```yaml
model: claude-sonnet-5
max_tokens: 4096
effort: low
```

For high-volume customer support, `effort: low` is the recommended setting. It cuts latency and cost without a meaningful drop in answer quality.

---

## 🔧 Environment variables

The full list is in [backend/.env.example](../backend/.env.example). Copy it to `.env` and fill in the real values.

| Variable                     | Description                                                                                                                                   | Required                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| `ANTHROPIC_API_KEY`          | API key for the LLM provider (Anthropic Claude).                                                                                              | Yes                      |
| `VOYAGE_API_KEY`             | API key for Voyage AI (RAG embeddings).                                                                                                       | Yes                      |
| `SUPABASE_URL`               | Supabase project URL.                                                                                                                         | Yes                      |
| `SUPABASE_ANON_KEY`          | Supabase public key, used by the frontend client.                                                                                             | Yes                      |
| `SUPABASE_SERVICE_ROLE_KEY`  | Supabase private key, used by the backend for privileged operations.                                                                          | Yes                      |
| `SUPABASE_SCHEMA`            | Database schema that holds Frontline's tables, functions, and views. Also add it in Supabase under Settings, API, Exposed schemas.            | No (default `frontline`) |
| `ALLOW_DEV_COMPANY_FALLBACK` | When `true`, requests without `Authorization: Bearer` use `DEV_COMPANY_ID`. Local development only: do not set it in staging or production.   | No (default `false`)     |
| `DEV_COMPANY_ID`             | UUID of the company used when the development fallback is on.                                                                                 | Dev only, with the flag  |
| `SSO_SHARED_SECRET`          | Secret shared with the external site. Verifies the incoming JWT (`sso_token`). The same value on both sides.                                  | Yes in staging/prod      |
| `FRONTLINE_SESSION_SECRET`   | Frontline-only secret (never shared with the site). Signs the internal session token, which lasts 24 hours.                                   | Yes in staging/prod      |
| `KV_REST_API_URL`            | REST URL of Frontline's Upstash database. Used to record `jti` values of SSO tokens that have already been used. Without it, SSO is rejected. | Yes in staging/prod      |
| `KV_REST_API_TOKEN`          | Private token for the same Upstash database. Do not commit the real value. Without it, SSO is rejected.                                       | Yes in staging/prod      |
| `FRONTEND_URL`               | Allowed CORS origin. Use `*` in development; in production set the exact frontend URL. Default: `*`.                                          | No                       |
| `CHAT_RATE_LIMIT`            | Per-IP request cap on the chat endpoint, in the form `<number>/<period>` (for example, `20/minute`, `200/hour`).                              | No (default `20/minute`) |
| `TRUST_PROXY_HEADERS`        | When `true`, the IP used for rate limiting is read from `X-Forwarded-For`. Enable it only behind a trusted reverse proxy.                     | No (default `false`)     |
| `LOG_LEVEL`                  | Minimum log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).                                                                          | No (default `INFO`)      |

> **Warning**: the `.env` file holds secrets and must never be committed. `.gitignore` keeps it out of version control.

---

## 🚀 Initial setup

1. From the `backend/` folder, copy the template:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` in an editor and replace the placeholder values with the real keys.

3. Check that loading works by starting the application (values are validated at startup):

   ```bash
   uvicorn main:app --reload
   ```

If a required variable is missing or malformed, startup fails with an explicit error.

---

## 📚 References

- **Code**: [backend/utils/config.py](../backend/utils/config.py)
- **Tests**: [backend/tests/utils/test_config.py](../backend/tests/utils/test_config.py)
- **`.env` template**: [backend/.env.example](../backend/.env.example)
- **Related docs**: [Logging](observability.md), [Repository structure](repo_structure.md)
- **External**: [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
