from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.vectorstore import delete_document, list_indexed_documents

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


@router.get("/documents")
async def documents_page(request: Request):
    documents = list_indexed_documents()
    for doc in documents:
        doc["size_display"] = _format_size(doc["size_bytes"])
    return templates.TemplateResponse(
        request,
        "documents.html",
        {"active": "documents", "documents": documents},
    )


@router.post("/documents/{filename}/delete")
async def delete_pdf(filename: str):
    file_path = settings.upload_dir / filename
    if file_path.exists():
        file_path.unlink()
    delete_document(filename)
    return RedirectResponse(url="/documents", status_code=303)
