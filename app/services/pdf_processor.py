from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def load_and_split_pdf(file_path: Path) -> list[Document]:
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()
    for page in pages:
        page.metadata["source"] = file_path.name
        page.metadata["file_path"] = str(file_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return splitter.split_documents(pages)
