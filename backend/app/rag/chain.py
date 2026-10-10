"""Final RAG step: retrieve -> prompt -> Groq LLM answer.

Strict grounding: the model may ONLY use the retrieved context. Anything
else gets the exact refusal sentence (checked in verification).
"""
import logging
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.rag.vectorstore import retrieve

logger = logging.getLogger(__name__)

REFUSAL = "I don't know based on the provided documents."
EMPTY_STORE = "No documents have been ingested yet. Run the ingestion script first."

SYSTEM_PROMPT = """You answer questions about the user's documents.
Rules:
1. Answer ONLY using the CONTEXT below. Never use outside knowledge.
2. If the context does not contain the answer, reply with exactly: """
SYSTEM_PROMPT += REFUSAL + """
3. Keep answers concise and factual."""


@lru_cache(maxsize=1)
def get_llm():
    """Singleton ChatGroq client (reads GROQ_API_KEY from env)."""
    from langchain_groq import ChatGroq  # lazy: keeps import time light

    return ChatGroq(model=settings.GROQ_MODEL, temperature=0)


def _build_context(hits) -> str:
    return "\n\n".join(
        f"[{chunk.source} p:{chunk.page}] {chunk.content}"
        for chunk, _ in hits
    )


async def answer_question(db: AsyncSession, question: str) -> tuple[str, list[str]]:
    """Retrieve top-k chunks, ask Groq with strict grounding. Returns (answer, sources)."""
    hits = await retrieve(db, question)
    if not hits:
        return EMPTY_STORE, []
    context = _build_context(hits)
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", f"CONTEXT:\n{context}\n\nQUESTION: {question}"),
    ]
    answer = (await get_llm().ainvoke(messages)).content
    if not isinstance(answer, str):
        answer = str(answer)
    sources = [chunk.chunk_id for chunk, _ in hits]
    logger.info("Q&A: %r -> %d sources", question[:80], len(sources))
    return answer.strip(), sources
