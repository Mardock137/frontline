<!-- markdownlint-disable -->
# RAG system

How Frontline's RAG (retrieval-augmented generation) system processes uploaded documents and runs semantic search.

---

## 📋 Contents

- [📄 Overview](#-overview)
- [⚙️ How it works](#️-how-it-works)
- [🔧 Configuration](#-configuration)
- [🚀 Quick start](#-quick-start)
- [🧪 Testing](#-testing)
- [🔍 Troubleshooting](#-troubleshooting)
- [⚠️ MVP notes](#️-mvp-notes)
- [📚 References](#-references)

---

## 📄 Overview

The RAG system lets each customer company:

1. **Upload documents** (PDF, DOCX, TXT, Markdown) from the dashboard.
2. Have them **indexed automatically**: text extraction, splitting into chunks, embedding, and storage.
3. **Search the knowledge base by meaning**: given a question, the system returns the most relevant chunks.

Semantic search is already a **tool** of the AI agent (`search_knowledge`). When a customer asks a question, the agent calls it on its own to look up answers in the knowledge base. The `/rag/search` endpoint stays available so you can test search directly, without going through the agent.

---

## ⚙️ How it works

### Ingestion flow

```txt
Uploaded file
   │
   ▼
[Supabase Storage] ──► raw file saved
   │
   ▼
[text_extraction] ──► text extracted
   │
   ▼
[chunking] ──────────► split into chunks of about 500 tokens, with overlap
   │
   ▼
[Voyage AI embed] ───► one 1024-dimension embedding per chunk
   │
   ▼
[document_chunks]  ── pgvector on Supabase
```

### Search flow

```text
"How do I reset my password?"
   │
   ▼
[Voyage AI embed] (input_type=query)
   │
   ▼
[frontline.match_document_chunks RPC] ── filter by company_id + ORDER BY distance
   │
   ▼
Top K chunks with a similarity score
```

### Technical choices

| Topic                | MVP choice                               | Why                                                                                  |
|----------------------|------------------------------------------|--------------------------------------------------------------------------------------|
| Embedding provider   | **Voyage AI** (`voyage-3`, 1024 dims)    | Multilingual, which the live chat needs, and strong quality.                         |
| SDK                  | REST via `httpx`                         | The official SDK does not support Python 3.14, so the call is made directly.         |
| Chunk size           | ~2000 characters (~500 tokens)           | A practical size for FAQs and manuals, and a common default.                         |
| Overlap              | ~200 characters                          | Keeps a key idea from being cut in half.                                             |
| Embedding batches    | 128 chunks per Voyage call               | The API maximum, split automatically.                                                |
| Vector index         | HNSW + cosine distance                   | pgvector's current default, a good balance of quality and speed.                     |
| Processing           | **Synchronous**, inside the upload endpoint | Simple. An async queue can come later.                                            |
| Table                | Separate `document_chunks`               | A document has many chunks, so they do not belong in one column on `documents`.      |
| Storage path         | `<company_id>/<document_id>/<filename>`  | A UUID in the path avoids collisions when two uploads share a filename.              |

---

## 🔧 Configuration

### Environment variables

| Variable                     | Where            | Description                                                                                          |
|------------------------------|------------------|------------------------------------------------------------------------------------------------------|
| `VOYAGE_API_KEY`             | `backend/.env`   | Voyage AI API key (from voyageai.com).                                                               |
| `SUPABASE_URL`               | `backend/.env`   | Supabase project URL.                                                                                 |
| `SUPABASE_SERVICE_ROLE_KEY`  | `backend/.env`   | Service role key (bypasses RLS; backend only).                                                        |
| `SUPABASE_SCHEMA`            | `backend/.env`   | Database schema (default `frontline`). Holds `document_chunks` and `match_document_chunks`.           |
| `ALLOW_DEV_COMPANY_FALLBACK` | `backend/.env`   | When `true`, a request with no session uses `DEV_COMPANY_ID`. Local development only (default `false`). |
| `DEV_COMPANY_ID`             | `backend/.env`   | UUID of the development company. Used only when the flag above is on.                                |

### Migrations

Run migrations `010`, `011`, and `012` in the Supabase SQL Editor **after** the earlier ones. See [database.md](database.md#-quick-start-applying-migrations).

---

## 🚀 Quick start

1. **Set `VOYAGE_API_KEY`** in `backend/.env`.
2. **Apply migrations** `010`, `011`, `012`, and `013` on Supabase.
3. **Start the backend**:

```bash
cd backend
uvicorn main:app --reload
```

4. **Upload a document** (locally this needs `ALLOW_DEV_COMPANY_FALLBACK=true`, otherwise the response is `401`):

```bash
curl -X POST http://localhost:8000/documents/upload \
     -F "file=@manual.pdf"
```

5. **Try a search** (again, without the flag the response is `401`):

```bash
curl -X POST http://localhost:8000/rag/search \
     -H "Content-Type: application/json" \
     -d '{"query": "How do I contact support?", "top_k": 5}'
```

---

## 🧪 Testing

```bash
cd backend
pytest tests/rag tests/api/test_documents.py tests/integrations/embedding_interfaces -v
```

Every test uses mocks. There are no real calls to Voyage, Supabase, or storage. The chunker and the extractor are tested end to end with real input (inline text, and a DOCX generated on the fly).

---

## 🔍 Troubleshooting

### `RuntimeError: Voyage is not configured`

**Cause**: `VOYAGE_API_KEY` is missing from `backend/.env`.
**Fix**: add it and restart the backend.

### Uploads are slow for large PDFs

**Cause**: in the MVP, processing happens synchronously inside the endpoint. A 100-page PDF can take a few seconds (parsing plus N embedding calls).
**Fix**: for the MVP, wait it out. After the MVP, processing can move to an async queue.

### `UnsupportedDocumentError`

**Cause**: the format is not PDF, DOCX, TXT, or Markdown.
**Fix**: convert the file to a supported format. Other formats (CSV, XLSX, HTML) are left for after the MVP.

### `/rag/search` returns an empty list

Possible causes:

- No document has been uploaded for that `company_id`.
- Documents were uploaded for a different company (another `DEV_COMPANY_ID`, if the local fallback is on, or another session).
- The documents' `status` is `error` (ingestion failed — check the backend logs).

### `extension "vector" is not available`, or an error on the HNSW index

**Cause**: migration `001_enable_extensions.sql` was not applied, or the Supabase project's pgvector version is too old.
**Fix**: in Supabase, under Database → Extensions, check that `vector` is enabled and up to date.

---

## ⚠️ MVP notes

- **Synchronous**: there is no background queue. An upload waits until ingestion finishes.
- **No automatic re-indexing**: if you change the chunking settings, existing chunks stay as they are. Delete the document and upload it again to regenerate them.
- **Character-based chunking**: a simple approximation. A real token splitter (for example, `tiktoken`) is an improvement for after the MVP.

---

## 📚 References

- **Code**:
  - [backend/rag/text_extraction.py](../backend/rag/text_extraction.py)
  - [backend/rag/chunking.py](../backend/rag/chunking.py)
  - [backend/rag/ingestion.py](../backend/rag/ingestion.py)
  - [backend/rag/search.py](../backend/rag/search.py)
  - [backend/integrations/embedding_interfaces/](../backend/integrations/embedding_interfaces/)
  - [backend/api/documents.py](../backend/api/documents.py)
- **Migrations**: [010](../backend/database/migrations/010_document_chunks.sql), [011](../backend/database/migrations/011_drop_documents_embedding.sql), [012](../backend/database/migrations/012_search_function.sql), [013](../backend/database/migrations/013_documents_with_counts_view.sql)
- **Tests**: [backend/tests/rag/](../backend/tests/rag/), [backend/tests/api/test_documents.py](../backend/tests/api/test_documents.py)
- **Related docs**: [architecture.md](architecture.md), [database.md](database.md), [api_endpoints.md](api_endpoints.md)
- **External**: [Voyage AI docs](https://docs.voyageai.com/), [pgvector](https://github.com/pgvector/pgvector)
