from fastapi import APIRouter, File, Request, UploadFile
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.pdf_processor import load_and_split_pdf
from app.services.vectorstore import index_documents

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))


@router.get("/")
async def upload_page(request: Request):
    return templates.TemplateResponse(
        request,
        "upload.html",
        {"active": "upload"},
    )


@router.post("/upload")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return templates.TemplateResponse(
            request,
            "upload.html",
            {
                "active": "upload",
                "error": "Only PDF files are supported.",
            },
            status_code=400,
        )

    destination = settings.upload_dir / file.filename
    if destination.exists():
        return templates.TemplateResponse(
            request,
            "upload.html",
            {
                "active": "upload",
                "error": f"'{file.filename}' already exists. Delete it first or rename the file.",
            },
            status_code=400,
        )

    content = await file.read()
    destination.write_bytes(content)

    chunks = load_and_split_pdf(destination)
    chunk_count = index_documents(chunks)

    return templates.TemplateResponse(
        request,
        "upload.html",
        {
            "active": "upload",
            "success": f"Uploaded '{file.filename}' and indexed {chunk_count} chunks.",
        },
    )
