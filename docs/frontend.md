<!-- markdownlint-disable -->
# Frontend

Frontline's frontend: the public live chat page and the Next.js project setup.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [⚙️ How it works](#️-how-it-works)
- [🔧 Configuration](#-configuration)
- [🚀 Quick start](#-quick-start)
- [🔍 Troubleshooting](#-troubleshooting)
- [⚠️ MVP notes](#️-mvp-notes)
- [📚 References](#-references)

---

## 📄 Overview

The frontend is a **Next.js 16** application with TypeScript and Tailwind CSS. It has four entry points:

- **`/chat/[slug]`** — public live chat for each customer company. No login.
- **`/dashboard`** — company dashboard for documents, tickets, agent configuration, and statistics. It opens through SSO from the external site (`/sso/callback`).
- **`/sso/callback`** — receives `sso_token` from the site, obtains the Frontline session, and redirects to the dashboard.
- **`/sso/error`** — shown when the token is missing, expired, or invalid, with a link back to the site when `NEXT_PUBLIC_WEBSITE_URL` is set.

---

## ⚙️ How it works

### Chat page flow

```txt
Customer opens /chat/[slug]
   │
   ▼
GET /chat/{slug}/config  ──► load branding (agent name, color, logo, welcome message)
   │
   ▼
Show a header with the branding, and the welcome message as the first agent message
   │
   ▼
Customer types a message
   │
   ▼
POST /chat/{slug}/message ──► send it to the backend with conversation_id (null on the first message)
   │
   ▼
Backend runs the AI agent ──► text reply
   │
   ▼
Show the agent's reply, and keep conversation_id for later messages
```

### Components — chat

| File                                  | Role                                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------------|
| `app/chat/[slug]/page.tsx`            | Main page: loads config, holds message and conversation state                        |
| `components/chat/ChatWindow.tsx`      | Message list with auto-scroll                                                        |
| `components/chat/MessageBubble.tsx`   | One bubble (customer on the right, agent on the left)                                |
| `components/chat/MessageInput.tsx`    | Text input and send button (Enter to send, Shift+Enter for a new line)               |
| `components/chat/TypingIndicator.tsx` | Three animated dots while the agent is working                                       |
| `lib/api.ts`                          | Chat calls the public backend; documents and dashboard call the `/api` proxy (the browser never attaches a Bearer token) |

### Components — dashboard

| File                                    | Role                                                                                          |
|-----------------------------------------|-----------------------------------------------------------------------------------------------|
| `app/dashboard/layout.tsx`              | Layout with a navigation sidebar (Documents / Tickets / Config / Stats)                       |
| `app/sso/callback/route.ts`             | Route handler: exchanges `sso_token`, stores the `httpOnly` cookie, redirects                 |
| `app/sso/error/page.tsx`                | SSO error, with a return link to the external site when the URL is set                        |
| `app/api/[...path]/route.ts`            | Proxy: forwards only `documents` and `dashboard`, and adds the Bearer token from the cookie. `POST`, `PATCH`, and `DELETE` from another origin return `403` |
| `app/dashboard/page.tsx`                | Redirects to `/dashboard/documents`                                                           |
| `lib/session.ts`                        | Session cookie name and lifetime (the browser never reads the cookie)                         |
| `app/dashboard/documents/page.tsx`      | Upload, list, and delete documents                                                            |
| `app/dashboard/tickets/page.tsx`        | Ticket list with status and escalation badges, and status changes                             |
| `app/dashboard/config/page.tsx`         | Agent configuration form (name, color, tone, language, welcome message)                       |
| `app/dashboard/stats/page.tsx`          | Stat cards and ticket-status bars                                                             |
| `components/ui/button.tsx`              | Button with variants (default / outline / ghost / and so on)                                  |
| `components/ui/card.tsx`                | Card with Header, Title, Description, Content, Footer                                         |
| `components/ui/badge.tsx`               | Colored badge for states (success / warning / error / info)                                   |
| `components/ui/table.tsx`               | Semantic table with Tailwind styling                                                          |
| `components/ui/input.tsx`               | Styled text input                                                                             |
| `components/ui/label.tsx`               | Form label                                                                                    |
| `components/ui/select.tsx`              | Styled dropdown with a chevron icon                                                           |
| `components/ui/textarea.tsx`            | Styled textarea                                                                               |
| `components/ui/dialog.tsx`              | Modal dialog with an overlay; closes on Escape and on an outside click                        |
| `components/ui/toast.tsx`               | Toast notifications, with `ToastProvider` and the `useToast()` hook                           |

### Dynamic branding

Each company has its own `primary_color` in `agent_configs`. The page applies that color to:

- the header background
- the customer's message bubbles
- the send button
- the input focus ring

If the company has a `logo_url`, it is shown in the header through `next/image`. Otherwise the header shows the first letter of the company name.

> `next.config.ts` sets `images.remotePatterns` to allow image URLs from any external domain (`hostname: "**"`). A multi-tenant product cannot predict logo domains in advance.

### Accessibility

The chat components are set up for screen readers and other assistive technology:

| Component              | What was added                                                                                          |
|------------------------|---------------------------------------------------------------------------------------------------------|
| `ChatWindow.tsx`       | `role="log"`, `aria-live="polite"`, `aria-relevant="additions"` on the message list                     |
| `MessageBubble.tsx`    | An `sr-only` label with the sender ("Assistant:" / "You:") before the text                              |
| `TypingIndicator.tsx`  | `role="status"`, `aria-live="polite"`, and `sr-only` text; the dots are `aria-hidden="true"`             |
| `MessageInput.tsx`     | `aria-label="Type a message"` on the textarea                                                           |
| `dashboard/layout.tsx` | `aria-label="Main navigation"` on the `nav`; `aria-current="page"` on the active link                   |

These are ARIA attributes only. They do not change behavior or how the page looks.

### Conversation handling

During the visit, `conversation_id` lives in a React ref. The first message sends `null`. The backend creates a conversation and returns the id, and the page stores it in `localStorage` under `support:conversation:<slug>`. On a later visit the page reads that id and loads the message history, with the welcome message still first. If the stored conversation no longer exists (`404`), the saved id is removed and the chat starts again from the welcome message. A transient failure (network, `500`) leaves the saved id in place, so a later refresh can try again.

Config loading uses an `AbortController`. If the user navigates away before the response arrives, the request is cancelled and state is not updated on a component that has already unmounted. `getConfig` in `lib/api.ts` accepts an optional `signal?: AbortSignal` for this.

---

## 🔧 Configuration

### Environment variables

The frontend reads `.env.local` in the `frontend/` folder (it is not committed):

| Variable                  | Description                                              | Development value       |
|---------------------------|----------------------------------------------------------|-------------------------|
| `NEXT_PUBLIC_API_URL`     | Base URL of the FastAPI backend                          | `http://localhost:8000` |
| `NEXT_PUBLIC_WEBSITE_URL` | External site URL (return link on `/sso/error`). Optional. | `https://example.com` |

Copy `frontend/.env.local.example` to `frontend/.env.local` and fill in the values. Leave `NEXT_PUBLIC_WEBSITE_URL` empty to hide the return link.

> Variables prefixed with `NEXT_PUBLIC_` are visible in the browser. Variables without that prefix stay on the server. In this MVP every frontend variable is public.

### Stack

| Technology               | Version | Role                                |
|--------------------------|---------|-------------------------------------|
| Next.js                  | 16.x    | React framework (App Router)        |
| React                    | 19.x    | UI                                  |
| TypeScript               | 5.x     | Types                               |
| Tailwind CSS             | 4.x     | Styling                             |
| class-variance-authority | 0.7.x   | CSS variants for UI components      |
| lucide-react             | 1.x     | Icons                               |
| clsx + tailwind-merge    | —       | Helpers for combining CSS classes   |

---

## 🚀 Quick start

Run every command from the `frontend/` folder.

1. **Install dependencies** (once):

```bash
npm install
```

2. **Create `.env.local`**:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSITE_URL=https://example.com
```

3. **Start the development server**:

```bash
npm run dev
```

4. **Open the chat** at `http://localhost:3000/chat/[slug]`
5. **Open the dashboard** at `http://localhost:3000/dashboard`

> The backend must be running at the same time, from the `backend/` folder, with `uvicorn main:app --reload`. Without it the frontend cannot load the configuration or send messages. Locally, the dashboard needs `ALLOW_DEV_COMPANY_FALLBACK=true` and `DEV_COMPANY_ID` in `backend/.env`.

---

## 🔍 Troubleshooting

### "Chat not found" when the page opens

**Cause**: the slug in the URL is not in the `companies` table, or that company has no row in `agent_configs`.
**Fix**: in Supabase, check that `companies` has a row with the slug from the URL and that `agent_configs` has a matching row.

### The page loads, but messages do not send

**Cause**: the backend is not running, or `NEXT_PUBLIC_API_URL` is wrong.
**Fix**: check that the backend responds at `http://localhost:8000/health` and that `.env.local` has the right URL.

### A CORS error in the browser

**Cause**: the public chat calls the backend cross-origin. The backend's `FRONTEND_URL` is missing, or the CORS middleware does not cover the frontend origin. The dashboard no longer sends the token cross-origin: documents and tickets go through `/api/...` on the same site.
**Fix**: set `FRONTEND_URL=*` (development) or the exact frontend URL (production) in `backend/.env`, then restart the backend.

> **Note**: with `FRONTEND_URL=*` the backend sets `allow_credentials=False`. The chat stays cross-origin and cookieless, so the wildcard is still appropriate. The dashboard no longer makes authenticated cross-origin calls.

---

## ⚠️ MVP notes

- **Public chat, dashboard via SSO**: `/chat/[slug]` is public. The dashboard opens through SSO from the external site (`/sso/callback`). Locally, with no cookie, the backend uses `DEV_COMPANY_ID` only when `ALLOW_DEV_COMPANY_FALLBACK=true`.
- **Document upload**: the file goes through the Next.js proxy. On Vercel, a file larger than 4.5 MB is rejected with `413`.
- **Conversation id**: kept in a React ref during the visit and in `localStorage` (`support:conversation:<slug>`) so a reload can restore the history. A `404` clears the saved id.
- **No automated tests**: the frontend has no automated tests in the MVP. UI tests are left for after the MVP.
- **Empty home page (`/`)**: the site root shows a placeholder. It is not a landing page yet.

---

## 📚 References

- **Chat**:
  - [frontend/app/chat/[slug]/page.tsx](../frontend/app/chat/%5Bslug%5D/page.tsx)
  - [frontend/components/chat/](../frontend/components/chat/)
- **Dashboard**:
  - [frontend/app/dashboard/](../frontend/app/dashboard/)
  - [frontend/components/ui/](../frontend/components/ui/)
- **API client**:
  - [frontend/lib/api.ts](../frontend/lib/api.ts)
  - [frontend/lib/session.ts](../frontend/lib/session.ts)
  - [frontend/app/api/[...path]/route.ts](../frontend/app/api/%5B...path%5D/route.ts)
  - [frontend/app/sso/](../frontend/app/sso/)
- **Related backend**:
  - [backend/api/config.py](../backend/api/config.py) — `GET /chat/{slug}/config`
  - [backend/api/agent.py](../backend/api/agent.py) — `POST /chat/{slug}/message`
  - [backend/api/documents.py](../backend/api/documents.py) — documents and RAG
  - [backend/api/dashboard.py](../backend/api/dashboard.py) — tickets, agent config, stats
- **Related docs**: [architecture.md](architecture.md), [api_endpoints.md](api_endpoints.md)
