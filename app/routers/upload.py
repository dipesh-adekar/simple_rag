from fastapi import APIRouter, File, Request, UploadFile
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.document_processor import is_supported, load_and_split_document
from app.services.vectorstore import index_documents

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))

SUPPORTED_LABEL = "PDF, TXT, Markdown, or DOCX"


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes / (1024 * 1024):.0f} MB"


def _upload_context(**extra):
    return {
        "active": "upload",
        "max_upload_size_mb": settings.max_upload_size_mb,
        **extra,
    }


@router.get("/")
async def upload_page(request: Request):
    return templates.TemplateResponse(
        request,
        "upload.html",
        _upload_context(),
    )


@router.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    if not file.filename or not is_supported(file.filename):
        return templates.TemplateResponse(
            request,
            "upload.html",
            _upload_context(error=f"Only {SUPPORTED_LABEL} files are supported."),
            status_code=400,
        )

    destination = settings.upload_dir / file.filename
    if destination.exists():
        return templates.TemplateResponse(
            request,
            "upload.html",
            _upload_context(
                error=f"'{file.filename}' already exists. Delete it first or rename the file.",
            ),
            status_code=400,
        )

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        return templates.TemplateResponse(
            request,
            "upload.html",
            _upload_context(
                error=(
                    f"'{file.filename}' is too large ({_format_size(len(content))}). "
                    f"Maximum size is {settings.max_upload_size_mb} MB."
                ),
            ),
            status_code=400,
        )

    if not content.strip():
        return templates.TemplateResponse(
            request,
            "upload.html",
            _upload_context(error=f"'{file.filename}' is empty."),
            status_code=400,
        )

    destination.write_bytes(content)

    try:
        chunks = load_and_split_document(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        return templates.TemplateResponse(
            request,
            "upload.html",
            _upload_context(error=f"Could not parse '{file.filename}'. The file may be corrupted."),
            status_code=400,
        )

    chunk_count = index_documents(chunks)

    return templates.TemplateResponse(
        request,
        "upload.html",
        _upload_context(
            success=f"Uploaded '{file.filename}' and indexed {chunk_count} chunks.",
        ),
    )
