import urllib.error
import urllib.request

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


def _check_ollama() -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return "ok" if response.status == 200 else "error"
    except (urllib.error.URLError, TimeoutError, OSError):
        return "unreachable"


@router.get("/health")
async def health():
    ollama_status = _check_ollama()
    return {
        "status": "ok",
        "ollama": ollama_status,
    }
