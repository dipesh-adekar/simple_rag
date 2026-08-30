from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.config import settings
from app.services.vectorstore import get_retriever

RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful assistant that answers questions based only on the provided context.
If the answer is not in the context, say you don't know based on the uploaded documents.

Context:
{context}

Question: {question}

Answer:"""
)


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )


def retrieve_context(question: str) -> tuple[str, list, list[str]]:
    retriever = get_retriever()
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    sources = sorted({doc.metadata.get("source", "unknown") for doc in docs})
    return context, docs, sources


def query_documents(question: str) -> dict:
    context, docs, sources = retrieve_context(question)
    prompt = RAG_PROMPT.format(context=context, question=question)
    llm = get_llm()
    answer = llm.invoke(prompt).content
    return {
        "answer": answer,
        "sources": sources,
        "context_chunks": len(docs),
    }


async def stream_answer(question: str):
    context, docs, sources = retrieve_context(question)
    prompt = RAG_PROMPT.format(context=context, question=question)
    llm = get_llm()
    async for chunk in llm.astream(prompt):
        if chunk.content:
            yield {"type": "token", "content": chunk.content}
    yield {
        "type": "done",
        "sources": sources,
        "context_chunks": len(docs),
    }
