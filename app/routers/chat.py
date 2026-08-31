import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.services.rag import query_documents, stream_answer
from app.services.vectorstore import list_indexed_documents

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))

NO_DOCUMENTS_MESSAGE = "No documents indexed yet. Upload a document first."


class ChatRequest(BaseModel):
    question: str
    source: str | None = None


def _validate_chat_request(source: str | None = None) -> None:
    documents = list_indexed_documents()
    if not documents:
        raise HTTPException(status_code=400, detail=NO_DOCUMENTS_MESSAGE)

    if source:
        known = {doc["filename"] for doc in documents}
        if source not in known:
            raise HTTPException(status_code=400, detail=f"Document '{source}' not found.")


@router.get("/chat")
async def chat_page(request: Request):
    documents = list_indexed_documents()
    return templates.TemplateResponse(
        request,
        "chat.html",
        {
            "active": "chat",
            "documents": documents,
            "has_documents": bool(documents),
        },
    )


@router.post("/chat/query")
async def chat_query(body: ChatRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    source = body.source.strip() if body.source else None
    _validate_chat_request(source=source)
    return query_documents(question, source=source)


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    source = body.source.strip() if body.source else None
    _validate_chat_request(source=source)

    async def event_generator():
        async for event in stream_answer(question, source=source):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
