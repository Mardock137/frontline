<!-- markdownlint-disable -->
# Repository structure

📁 frontline/
 │
 ├── 📁 backend/                                                         # Backend source (Python + FastAPI).
 │    ├── 📁 .venv/                                                      # Virtual environment with the installed dependencies.
 │    ├── 📁 agents/                                                     # AI agents and their logic.
 │    │    ├── 📄 base_agent.py                                          # Shared base class for every agent.
 │    │    └── 📄 support_agent.py                                       # Support agent: autonomous loop with tool calling. Saves messages to the database.
 │    ├── 📁 api/                                                        # HTTP endpoints the backend exposes to the frontend.
 │    │    ├── 📄 agent.py                                               # Chat endpoints: POST /chat/{company_slug}/message and GET /chat/{company_slug}/conversation/{id}/messages.
 │    │    ├── 📄 auth.py                                                # POST /auth/sso: exchanges the external site's token for a Frontline session.
 │    │    ├── 📄 config.py                                              # Public GET /chat/{company_slug}/config (branding and welcome message).
 │    │    ├── 📄 dashboard.py                                           # /dashboard/* endpoints: tickets, agent-config, stats (tenant from the session).
 │    │    └── 📄 documents.py                                           # /documents/* and /rag/search (tenant from the session).
 │    ├── 📁 config/                                                     # Configuration.
 │    │    ├── 📁 llm_models/                                            # LLM settings for each agent.
 │    │    │    ├── 📄 loader.py                                         # YAML loader: reads and validates LLMModelConfig (model, max_tokens, effort).
 │    │    │    └── 📄 support_agent.yaml                                # Model settings for the support agent (model, max_tokens, effort).
 │    │    └── 📁 prompts/
 │    │         └── 📄 support_agent.py                                  # System prompt template: agent identity, tone, tool instructions.
 │    ├── 📁 database/                                                   # Data models (Pydantic), the Supabase client, and SQL migrations.
 │    │    ├── 📁 migrations/                                            # SQL migrations to run by hand in the Supabase SQL Editor, in numeric order. Tables, functions, and views are created in the dedicated "frontline" schema.
 │    │    │    ├── 📄 001_enable_extensions.sql                         # Creates the dedicated "extensions" and "frontline" schemas. Enables pgvector in "extensions", and pgcrypto.
 │    │    │    ├── 📄 002_companies.sql                                 # companies table (tenants).
 │    │    │    ├── 📄 003_users.sql                                     # users table (dashboard users, reserved for later). Removed by migration 019. Never used.
 │    │    │    ├── 📄 004_agent_configs.sql                             # agent_configs table (per-company agent configuration).
 │    │    │    ├── 📄 005_documents.sql                                 # documents table (knowledge base), originally with an embedding column for RAG.
 │    │    │    ├── 📄 006_conversations.sql                             # conversations table (live chat).
 │    │    │    ├── 📄 007_messages.sql                                  # messages table (messages inside a conversation).
 │    │    │    ├── 📄 008_tickets.sql                                   # tickets table (unresolved cases and escalations).
 │    │    │    ├── 📄 009_storage.sql                                   # Private Supabase Storage bucket "documents".
 │    │    │    ├── 📄 010_document_chunks.sql                           # document_chunks table with a vector(1024) embedding for RAG.
 │    │    │    ├── 📄 011_drop_documents_embedding.sql                  # Drops the embedding column from documents (it now lives on document_chunks).
 │    │    │    ├── 📄 012_search_function.sql                           # SQL function match_document_chunks for multi-tenant semantic search.
 │    │    │    ├── 📄 013_documents_with_counts_view.sql                # documents_with_counts view, exposing the chunk count per document.
 │    │    │    ├── 📄 014_tickets_add_is_escalation.sql                 # Adds the is_escalation boolean column to tickets.
 │    │    │    ├── 📄 015_documents_with_counts_security_invoker.sql    # Sets security_invoker=true on the documents_with_counts view (Security Advisor fix).
 │    │    │    ├── 📄 016_fix_functions_search_path.sql                 # Pins search_path on set_updated_at and match_document_chunks (Security Advisor fix).
 │    │    │    ├── 📄 017_revoke_rls_auto_enable_execute.sql            # Revokes execute on rls_auto_enable() from anon and authenticated (Security Advisor fix).
 │    │    │    ├── 📄 018_revoke_rls_auto_enable_execute_public.sql     # Revokes execute on rls_auto_enable() from PUBLIC, the real source of the grant inherited by anon and authenticated.
 │    │    │    ├── 📄 019_drop_users_table.sql                          # Drops the users table. No endpoint ever used it.
 │    │    │    └── 📄 020_grant_frontline_privileges.sql                # Grants service_role privileges on the frontline schema (fixes 403/42501 on a custom schema).
 │    │    ├── 📄 models.py                                              # Pydantic models for the database tables.
 │    │    └── 📄 supabase_client.py                                     # Cached factory for the Supabase client (service role).
 │    ├── 📁 integrations/                                               # Clients for external APIs.
 │    │    ├── 📁 embedding_interfaces/                                  # Interface for embedding providers.
 │    │    │    ├── 📄 base_embedding_interface.py                       # Abstract interface for embedding providers.
 │    │    │    └── 📄 voyage_embedding.py                               # Voyage AI implementation over REST (httpx).
 │    │    └── 📁 llm_interfaces/                                        # Interface for LLM providers.
 │    │         ├── 📄 base_llm_interface.py                             # Abstract interface with chat(messages, system, tools). ChatResponse and ToolUse dataclasses.
 │    │         └── 📄 anthropic_interface.py                            # Concrete Anthropic Claude adapter with tool calling (AsyncAnthropic SDK).
 │    ├── 📁 logs/                                                       # Log files written at runtime.
 │    ├── 📁 rag/                                                        # RAG system: document processing, embeddings, and semantic search.
 │    │    ├── 📄 chunking.py                                            # Splits text into chunks with overlap.
 │    │    ├── 📄 ingestion.py                                           # End-to-end pipeline: upload, extract, chunk, embed, save.
 │    │    ├── 📄 search.py                                              # Semantic search over chunks through match_document_chunks.
 │    │    └── 📄 text_extraction.py                                     # Extracts text from PDF, DOCX, TXT, and Markdown.
 │    ├── 📁 tests/                                                      # Automated tests for the functions and modules.
 │    │    ├── 📄 conftest.py                                            # Fixtures shared by every test (company_id, conversation_id).
 │    │    ├── 📁 agents/                                                # Agent tests.
 │    │    │    ├── 📄 test_base_agent.py
 │    │    │    └── 📄 test_support_agent.py                             # Tests the agent loop (LLM and tools are mocked).
 │    │    ├── 📁 api/                                                   # HTTP endpoint tests.
 │    │    │    ├── 📄 test_agent.py                                     # Tests /chat/{slug}/message (Supabase and the agent are mocked).
 │    │    │    ├── 📄 test_auth.py                                      # Tests POST /auth/sso: session, expired or reused token, missing `jti` or `product`, Redis unavailable (`503`).
 │    │    │    ├── 📄 test_config.py                                    # Tests /chat/{slug}/config (Supabase is mocked).
 │    │    │    ├── 📄 test_dashboard.py                                 # Tests /dashboard/* (14 tests, Supabase mocked), including 401 with no session.
 │    │    │    └── 📄 test_documents.py
 │    │    ├── 📁 config/                                                # Configuration tests.
 │    │    │    └── 📄 test_llm_models_loader.py                         # YAML loader tests (happy path, errors, validation).
 │    │    ├── 📁 database/                                              # Tests for the data models and the Supabase client.
 │    │    │    ├── 📄 test_models.py                                    # Tests the Pydantic database models.
 │    │    │    └── 📄 test_supabase_client.py                           # Tests the Supabase client.
 │    │    ├── 📁 integrations/                                          # Integration tests.
 │    │    │    ├── 📁 embedding_interfaces/
 │    │    │    │    └── 📄 test_voyage_embedding.py
 │    │    │    └── 📁 llm_interfaces/
 │    │    │         ├── 📄 test_base_llm_interface.py                   # Tests the base interface, ChatResponse, and ToolUse.
 │    │    │         └── 📄 test_anthropic_interface.py                  # Tests AnthropicInterface with the YAML and the SDK mocked.
 │    │    ├── 📁 rag/                                                   # RAG tests.
 │    │    │    ├── 📄 test_chunking.py
 │    │    │    ├── 📄 test_ingestion.py
 │    │    │    ├── 📄 test_search.py
 │    │    │    └── 📄 test_text_extraction.py
 │    │    ├── 📁 tools/                                                 # Tests for the agent's tools.
 │    │    │    ├── 📄 test_escalation.py                                # Tests escalate (Supabase is mocked).
 │    │    │    ├── 📄 test_knowledge.py                                 # Tests search_knowledge (search_chunks is mocked).
 │    │    │    └── 📄 test_ticket.py                                    # Tests create_ticket (Supabase is mocked).
 │    │    ├── 📁 utils/                                                 # Utility tests.
 │    │    │    ├── 📄 test_auth.py                                      # Tests external-site JWT verification (`jti`, `product`), the internal session, and the DEV_COMPANY_ID fallback only when the flag is on.
 │    │    │    ├── 📄 test_config.py
 │    │    │    ├── 📄 test_logging_config.py
 │    │    │    └── 📄 test_replay_guard.py                              # Tests the single-use check: new `jti`, already used, HTTP error, timeout, missing variables. No real calls.
 │    │    └── 📄 test_main.py                                           # Tests the application entry point.
 │    ├── 📁 tools/                                                      # Tools the AI agent can call on its own.
 │    │    ├── 📄 knowledge.py                                           # search_knowledge: semantic search over the knowledge base.
 │    │    ├── 📄 ticket.py                                              # create_ticket: writes a support ticket to the database.
 │    │    └── 📄 escalation.py                                          # escalate: creates an escalation ticket and updates the conversation status.
 │    ├── 📁 utils/                                                      # Shared utilities and configuration.
 │    │    ├── 📄 auth.py                                                # Verifies the external site's JWT (`jti` and `product` are required), the internal session token, and the get_current_company_id dependency.
 │    │    ├── 📄 config.py                                              # Loads and reads environment variables from .env.
 │    │    ├── 📄 logging_config.py                                      # Central logging setup (console and file, rotation, format).
 │    │    └── 📄 replay_guard.py                                        # Records the SSO token's `jti` in Upstash (single use). If Redis does not respond, sign-in is rejected.
 │    ├── 📄 .dockerignore                                               # Files and folders left out of the Docker build context (venv, tests, logs, secrets).
 │    ├── 📄 .env                                                        # API keys and private environment variables.
 │    ├── 📄 .env.example                                                # Example of the environment variables in use.
 │    ├── 📄 Dockerfile                                                  # Backend Docker image (Python 3.14-slim), used for the Cloud Run deploy.
 │    ├── 📄 main.py                                                     # Backend entry point: creates the FastAPI app and registers endpoints and middleware.
 │    ├── 📄 pytest.ini                                                  # pytest configuration.
 │    └── 📄 requirements.txt                                            # Python dependencies and their versions.
 │
 ├── 📁 dev_support/                                                     # Local notes. Not documentation, and not versioned.
 │    ├── 📄 notes.md
 │    ├── 📄 to_do_list.md
 │    └── 📄 whiteboard.md
 │
 ├── 📁 docs/                                                            # Operational and technical documentation.
 │    ├── 📄 api_endpoints.md                                            # List of HTTP API endpoints.
 │    ├── 📄 architecture.md                                             # System architecture, stack, and database schema.
 │    ├── 📄 database.md                                                 # How to apply the Supabase migrations, and how the schema is structured.
 │    ├── 📄 deploy.md                                                   # Staging deploy (Cloud Run + Vercel).
 │    ├── 📄 rag.md                                                      # RAG guide (upload, chunking, embedding, search).
 │    ├── 📄 config.md                                                   # Configuration guide.
 │    ├── 📄 frontend.md                                                 # Frontend guide: public live chat and Next.js setup.
 │    ├── 📄 observability.md                                            # Logging system.
 │    └── 📄 repo_structure.md                                           # This file: layout of the repository.
 │
 ├── 📁 frontend/                                                        # Frontend source (Next.js 16 + Tailwind CSS v4).
 │    ├── 📁 app/                                                        # Next.js App Router.
 │    │    ├── 📁 api/
 │    │    │    └── 📁 [...path]/
 │    │    │         └── 📄 route.ts                                     # Proxy: forwards documents and dashboard, adds the Bearer token from the cookie. POST, PATCH, and DELETE from another origin return 403.
 │    │    ├── 📁 chat/
 │    │    │    └── 📁 [slug]/
 │    │    │         └── 📄 page.tsx                                     # Public live chat page: loads config, shows the welcome message, handles the conversation.
 │    │    ├── 📁 sso/
 │    │    │    ├── 📁 callback/
 │    │    │    │    └── 📄 route.ts                                     # Exchanges sso_token for a session cookie and redirects to /dashboard.
 │    │    │    └── 📁 error/
 │    │    │         └── 📄 page.tsx                                     # SSO error, with a return link to the external site when the URL is set.
 │    │    ├── 📁 dashboard/                                             # Company dashboard (admin area).
 │    │    │    ├── 📁 config/
 │    │    │    │    └── 📄 page.tsx                                     # Form for agent_name, color, tone, language, and welcome message.
 │    │    │    ├── 📁 documents/
 │    │    │    │    └── 📄 page.tsx                                     # Upload, list, and delete documents.
 │    │    │    ├── 📁 stats/
 │    │    │    │    └── 📄 page.tsx                                     # Stat cards: conversations, tickets by status, open escalations.
 │    │    │    ├── 📁 tickets/
 │    │    │    │    └── 📄 page.tsx                                     # Ticket list with status and escalation badges, and status changes.
 │    │    │    ├── 📄 layout.tsx                                        # Layout with a navigation sidebar (Documents / Tickets / Config / Stats).
 │    │    │    └── 📄 page.tsx                                          # Redirects to /dashboard/documents.
 │    │    ├── 📄 globals.css                                            # Global styles (Tailwind v4).
 │    │    ├── 📄 layout.tsx                                             # Root layout of the app.
 │    │    └── 📄 page.tsx                                               # Home page placeholder.
 │    ├── 📁 components/
 │    │    ├── 📁 chat/
 │    │    │    ├── 📄 ChatWindow.tsx                                    # Message list with automatic scrolling.
 │    │    │    ├── 📄 MessageBubble.tsx                                 # One message bubble (agent / customer).
 │    │    │    ├── 📄 MessageInput.tsx                                  # Textarea and send button.
 │    │    │    └── 📄 TypingIndicator.tsx                               # "Typing..." animation.
 │    │    └── 📁 ui/                                                    # Reusable UI components (shadcn/ui style, Tailwind v4).
 │    │         ├── 📄 badge.tsx                                         # Colored badge for states (success / warning / error / info).
 │    │         ├── 📄 button.tsx                                        # Button with variants (default / outline / ghost / destructive / link).
 │    │         ├── 📄 card.tsx                                          # Card with Header, Title, Description, Content, Footer.
 │    │         ├── 📄 dialog.tsx                                        # Modal dialog with an overlay. Closes on Escape.
 │    │         ├── 📄 input.tsx                                         # Styled text input.
 │    │         ├── 📄 label.tsx                                         # Form label.
 │    │         ├── 📄 select.tsx                                        # Dropdown with a chevron icon.
 │    │         ├── 📄 table.tsx                                         # Semantic table with Tailwind styling.
 │    │         ├── 📄 textarea.tsx                                      # Styled textarea.
 │    │         └── 📄 toast.tsx                                         # Toast notification: ToastProvider and the useToast() hook.
 │    ├── 📁 lib/
 │    │    ├── 📄 api.ts                                                 # Chat calls the backend. Documents and dashboard call the /api proxy (the browser does not attach a Bearer token).
 │    │    ├── 📄 session.ts                                             # Session cookie name and lifetime (the browser never reads it).
 │    │    └── 📄 utils.ts                                               # cn() helper for conditional Tailwind classes.
 │    ├── 📄 .env.local                                                  # Local environment variables (NEXT_PUBLIC_API_URL).
 │    ├── 📄 .env.local.example                                          # Example frontend environment variables.
 │    ├── 📄 next.config.ts                                              # Next.js configuration.
 │    ├── 📄 package.json                                                # npm dependencies and scripts.
 │    ├── 📄 postcss.config.mjs                                          # PostCSS configuration for Tailwind v4.
 │    └── 📄 tsconfig.json                                               # TypeScript configuration.
 │
 ├── 📁 .github/                                                         # GitHub CI automation.
 │    └── 📁 workflows/
 │         ├── 📄 backend-ci.yml                                         # GitHub Actions workflow: installs the backend and runs pytest on pull requests.
 │         └── 📄 frontend-ci.yml                                        # GitHub Actions workflow: installs the frontend and runs lint and build on pull requests.
 │
 ├── 📄 .gitignore                                                       # Files and folders excluded from version control.
 ├── 📄 CHANGELOG.md                                                     # Version history.
 └── 📄 README.md                                                        # Overview, setup, and a short guide to the project.
