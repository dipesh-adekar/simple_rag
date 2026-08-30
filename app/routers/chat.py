from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.rag import query_documents

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))


@router.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat", "messages": []},
    )


@router.post("/chat")
async def chat_query(request: Request, question: str = Form(...)):
    result = query_documents(question.strip())
    messages = [
        {"role": "user", "content": question.strip()},
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "context_chunks": result["context_chunks"],
        },
    ]
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat", "messages": messages},
    )
