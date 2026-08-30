# Local RAG with Ollama

A simple RAG pipeline: upload PDFs, index them with Ollama embeddings, and chat against your documents using a local LLM.

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Uvicorn |
| UI | Jinja2 templates + plain CSS |
| LLM | Ollama — `qwen2.5:14b` |
| Embeddings | Ollama — `nomic-embed-text` |
| RAG orchestration | LangChain |
| PDF parsing | PyPDF |
| Vector store | ChromaDB (persisted on disk) |
| Deployment | Docker + Docker Compose |

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

Uploaded PDFs and the Chroma index are persisted in `./data/uploads` and `./data/chroma`.

## Usage

1. **Upload** — go to `/`, upload a PDF. It is saved and chunked/indexed automatically.
2. **Documents** — go to `/documents` to see indexed PDFs and delete them.
3. **Chat** — go to `/chat` and ask questions against all uploaded documents.

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
