from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.config import settings
from app.services.vectorstore import search_with_scores

RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful assistant that answers questions based only on the provided context.
If the answer is not in the context, say you don't know based on the uploaded documents.

Context:
{context}

Question: {question}

Answer:"""
)

NO_CONTEXT_MESSAGE = (
    "I couldn't find relevant information in your uploaded documents for this question."
)


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )


def _build_snippets(results: list[tuple]) -> list[dict]:
    return [
        {
            "source": doc.metadata.get("source", "unknown"),
            "text": doc.page_content,
            "score": round(score, 4),
        }
        for doc, score in results
    ]


def retrieve_context(question: str, source: str | None = None) -> tuple[str, list, list[str], list[dict], bool]:
    results = search_with_scores(question, source=source)

    if not results:
        return "", [], [], [], False

    best_distance = results[0][1]
    if best_distance > settings.max_retrieval_distance:
        return "", [], [], [], False

    docs = [doc for doc, _ in results]
    context = "\n\n".join(doc.page_content for doc in docs)
    sources = sorted({doc.metadata.get("source", "unknown") for doc in docs})
    snippets = _build_snippets(results)
    return context, docs, sources, snippets, True


def query_documents(question: str, source: str | None = None) -> dict:
    context, docs, sources, snippets, relevant = retrieve_context(question, source=source)

    if not relevant:
        return {
            "answer": NO_CONTEXT_MESSAGE,
            "sources": [],
            "context_chunks": 0,
            "snippets": [],
            "relevant": False,
        }

    prompt = RAG_PROMPT.format(context=context, question=question)
    llm = get_llm()
    answer = llm.invoke(prompt).content
    return {
        "answer": answer,
        "sources": sources,
        "context_chunks": len(docs),
        "snippets": snippets,
        "relevant": True,
    }


async def stream_answer(question: str, source: str | None = None):
    context, docs, sources, snippets, relevant = retrieve_context(question, source=source)

    if not relevant:
        yield {"type": "token", "content": NO_CONTEXT_MESSAGE}
        yield {
            "type": "done",
            "sources": [],
            "context_chunks": 0,
            "snippets": [],
            "relevant": False,
        }
        return

    prompt = RAG_PROMPT.format(context=context, question=question)
    llm = get_llm()
    async for chunk in llm.astream(prompt):
        if chunk.content:
            yield {"type": "token", "content": chunk.content}
    yield {
        "type": "done",
        "sources": sources,
        "context_chunks": len(docs),
        "snippets": snippets,
        "relevant": True,
    }
