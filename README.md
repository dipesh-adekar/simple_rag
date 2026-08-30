# Local RAG with Ollama

A simple RAG pipeline: upload documents, index them with Ollama embeddings, and chat against your files using a local LLM.

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Uvicorn |
| UI | Jinja2 templates + plain CSS |
| LLM | Ollama — `qwen2.5:14b` |
| Embeddings | Ollama — `nomic-embed-text` |
| RAG orchestration | LangChain |
| Document parsing | PyPDF, TextLoader, Docx2txt |
| Vector store | ChromaDB (persisted on disk) |
| Deployment | Docker + Docker Compose |

## Supported file types

- PDF (`.pdf`)
- Plain text (`.txt`)
- Markdown (`.md`)
- Word (`.docx`)

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) running locally with models pulled:

```bash
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000

## Docker Compose

Uses your host Ollama instance via `host.docker.internal`:

```bash
docker compose up --build
```

Open http://localhost:8000

Uploaded files and the Chroma index are persisted in `./data/uploads` and `./data/chroma`.

## Usage

1. **Upload** — go to `/`, upload a PDF, text file, Markdown, or DOCX. It is saved and chunked/indexed automatically.
2. **Documents** — go to `/documents` to see indexed files, chunk counts, and delete them.
3. **Chat** — go to `/chat`, optionally filter to one document, and ask questions. Expand "Context used" to inspect retrieved chunks.

## Learning features

| Feature | What it teaches |
|---------|-----------------|
| Per-document filter | Metadata-scoped vector search |
| Relevance threshold | When not to call the LLM |
| Context snippets | Debugging retrieval quality |
| Chunk counts | How chunking affects indexing |
| Multi-format upload | Ingestion vs retrieval pipeline |

## Configuration

Set via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `LLM_MODEL` | `qwen2.5:14b` | Chat model |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | `200` | Chunk overlap |
| `RETRIEVAL_K` | `4` | Chunks retrieved per query |
| `MAX_RETRIEVAL_DISTANCE` | `1.0` | Max L2 distance for the best match; higher = stricter |

Lower distance scores mean better matches. If the best retrieved chunk exceeds `MAX_RETRIEVAL_DISTANCE`, the app skips the LLM and returns a "no relevant context" message.

## Tests

Smoke tests use fake embeddings and a mocked LLM — no Ollama required:

```bash
pytest
```
