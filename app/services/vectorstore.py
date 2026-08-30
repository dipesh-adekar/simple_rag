from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from app.config import settings


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name="pdf_documents",
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def index_documents(chunks: list[Document]) -> int:
    if not chunks:
        return 0
    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    return len(chunks)


def delete_document(filename: str) -> None:
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    results = collection.get(where={"source": filename})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def list_indexed_documents() -> list[dict]:
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    results = collection.get(include=["metadatas"])
    seen: dict[str, dict] = {}
    for metadata in results.get("metadatas") or []:
        if not metadata:
            continue
        source = metadata.get("source")
        if not source or source in seen:
            continue
        file_path = Path(metadata.get("file_path", settings.upload_dir / source))
        seen[source] = {
            "filename": source,
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        }
    return sorted(seen.values(), key=lambda item: item["filename"].lower())


def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": settings.retrieval_k})
