import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.services.rag import query_documents, stream_answer
from app.services.vectorstore import list_indexed_documents

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))


class ChatRequest(BaseModel):
    question: str
    source: str | None = None


@router.get("/chat")
async def chat_page(request: Request):
    documents = list_indexed_documents()
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat", "documents": documents},
    )


@router.post("/chat/query")
async def chat_query(body: ChatRequest):
    question = body.question.strip()
    source = body.source.strip() if body.source else None
    result = query_documents(question, source=source)
    return result


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    question = body.question.strip()
    source = body.source.strip() if body.source else None

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
