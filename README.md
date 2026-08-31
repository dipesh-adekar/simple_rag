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

## Quick start

```bash
make dev      # start locally with reload
make test     # run smoke tests
make docker-up
```

Or manually:

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

## Features

| Feature | Description |
|---------|-------------|
| Per-document filter | Scope chat to a single uploaded file |
| Relevance threshold | Skip the LLM when retrieval scores are weak |
| Context snippets | Inspect retrieved chunks under each answer |
| Chunk counts | See how many chunks each file produced |
| Multi-format upload | PDF, TXT, Markdown, DOCX |
| Empty-index guard | Chat is disabled until documents are indexed |
| Upload validation | File type, size, and empty-file checks |
| Health check | `GET /health` reports app and Ollama status |
| Chat history | Last 50 messages persisted in the browser |
| Markdown answers | Assistant replies render basic markdown |

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
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum upload size in megabytes |

Lower distance scores mean better matches. If the best retrieved chunk exceeds `MAX_RETRIEVAL_DISTANCE`, the app skips the LLM and returns a "no relevant context" message.

## Health check

```bash
curl http://localhost:8000/health
```

Example response:

```json
{"status": "ok", "ollama": "ok"}
```

## Tests

Smoke tests use fake embeddings and a mocked LLM — no Ollama required:

```bash
pytest
```
