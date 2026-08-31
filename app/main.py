from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import chat, documents, health, upload

app = FastAPI(title="Local RAG", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(settings.base_dir / "static")), name="static")

app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(health.router)
