import pytest
from langchain_community.embeddings import FakeEmbeddings
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag import NO_CONTEXT_MESSAGE


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    chroma_dir = tmp_path / "chroma"
    upload_dir.mkdir()
    chroma_dir.mkdir()
    monkeypatch.setattr("app.config.settings.upload_dir", upload_dir)
    monkeypatch.setattr("app.config.settings.chroma_dir", chroma_dir)
    monkeypatch.setattr("app.config.settings.max_retrieval_distance", 10_000.0)
    return {"upload_dir": upload_dir, "chroma_dir": chroma_dir}


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    monkeypatch.setattr(
        "app.services.vectorstore.get_embeddings",
        lambda: FakeEmbeddings(size=384),
    )


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    class FakeResponse:
        content = "Mocked answer from the LLM."

    class FakeLLM:
        def invoke(self, prompt):
            return FakeResponse()

        async def astream(self, prompt):
            for token in ["Mocked ", "answer"]:
                chunk = FakeResponse()
                chunk.content = token
                yield chunk

    monkeypatch.setattr("app.services.rag.get_llm", lambda: FakeLLM())


@pytest.fixture
def client(isolated_settings):
    return TestClient(app)


def upload_text(client: TestClient, filename: str, content: str):
    return client.post(
        "/upload",
        files={"file": (filename, content.encode(), "text/plain")},
    )


def test_upload_indexes_text_document(client):
    response = upload_text(client, "notes.txt", "Python is a programming language used for many tasks.")
    assert response.status_code == 200
    assert "indexed" in response.text

    docs_page = client.get("/documents")
    assert docs_page.status_code == 200
    assert "notes.txt" in docs_page.text
    assert "Chunks" in docs_page.text


def test_chat_returns_snippets(client):
    upload_text(client, "facts.txt", "The capital of France is Paris.")

    response = client.post("/chat/query", json={"question": "What is the capital of France?"})
    assert response.status_code == 200

    data = response.json()
    assert data["relevant"] is True
    assert data["answer"] == "Mocked answer from the LLM."
    assert data["context_chunks"] > 0
    assert len(data["snippets"]) > 0
    assert data["snippets"][0]["source"] == "facts.txt"
    assert "Paris" in data["snippets"][0]["text"]


def test_source_filter_limits_retrieval(client):
    upload_text(client, "animals.txt", "Cats are independent pets.")
    upload_text(client, "cars.txt", "Electric cars use batteries for power.")

    response = client.post(
        "/chat/query",
        json={"question": "Tell me about batteries", "source": "cars.txt"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["relevant"] is True
    assert data["sources"] == ["cars.txt"]
    assert all(snippet["source"] == "cars.txt" for snippet in data["snippets"])


def test_relevance_threshold_blocks_answer(client, monkeypatch):
    upload_text(client, "notes.txt", "Some indexed content about databases.")

    monkeypatch.setattr("app.config.settings.max_retrieval_distance", -0.001)

    response = client.post("/chat/query", json={"question": "What about databases?"})
    assert response.status_code == 200

    data = response.json()
    assert data["relevant"] is False
    assert data["answer"] == NO_CONTEXT_MESSAGE
    assert data["snippets"] == []


def test_unsupported_upload_is_rejected(client):
    response = client.post(
        "/upload",
        files={"file": ("script.exe", b"binary", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "supported" in response.text.lower()
