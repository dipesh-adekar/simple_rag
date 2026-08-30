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


def query_documents(question: str) -> dict:
    retriever = get_retriever()
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = RAG_PROMPT.format(context=context, question=question)
    llm = get_llm()
    answer = llm.invoke(prompt).content
    sources = sorted({doc.metadata.get("source", "unknown") for doc in docs})
    return {
        "answer": answer,
        "sources": sources,
        "context_chunks": len(docs),
    }
