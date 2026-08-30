import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.services.rag import query_documents, stream_answer

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))


class ChatRequest(BaseModel):
    question: str


@router.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat"},
    )


@router.post("/chat/query")
async def chat_query(body: ChatRequest):
    result = query_documents(body.question.strip())
    return result


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    question = body.question.strip()

    async def event_generator():
        async for event in stream_answer(question):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
