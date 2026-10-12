"""Final RAG step: retrieve -> prompt -> Groq LLM answer.

Session-aware: prior turns of THIS conversation are used to (1) rewrite
follow-ups into standalone queries for retrieval and (2) give the answer
model conversational context. Strict grounding holds: only document CONTEXT
is a source of facts; the conversation is context, never evidence.
Cross-session isolation is structural — history is always loaded per
conversation_id by the caller, so other threads are invisible here.
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
2. The CONVERSATION is prior chat for understanding references (like "his" or
   "it"). It is NOT a source of facts — never quote it as evidence.
3. If the context does not contain the answer, reply with exactly: """
SYSTEM_PROMPT += REFUSAL + """
4. Keep answers concise and factual."""

REWRITE_PROMPT = """Rewrite the follow-up question as a standalone question using the
conversation above. Rules: resolve pronouns/references from the conversation,
keep it to one sentence, output ONLY the rewritten question, never answer it.
If it is already standalone, repeat it unchanged."""


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


def _build_history(history: list[tuple[str, str]]) -> str:
    return "\n".join(
        f"{'User' if role == 'user' else 'Assistant'}: {text}"
        for role, text in history
    )


async def rewrite_question(question: str, history: list[tuple[str, str]]) -> str:
    """Follow-up -> standalone query. Skipped (no LLM call) when no history."""
    if not history:
        return question
    rewritten = (
        await get_llm().ainvoke(
            [("human", f"CONVERSATION:\n{_build_history(history)}\n\n{REWRITE_PROMPT}\n\nFOLLOW-UP: {question}")]
        )
    ).content
    if not isinstance(rewritten, str):
        rewritten = str(rewritten)
    rewritten = rewritten.strip().strip('"')
    logger.info("Rewrite: %r -> %r", question[:80], rewritten[:120])
    return rewritten or question


async def answer_question(
    db: AsyncSession,
    question: str,
    history: list[tuple[str, str]] | None = None,
) -> tuple[str, list[str]]:
    """Retrieve top-k chunks, ask Groq with strict grounding. Returns (answer, sources)."""
    history = history or []
    search_query = await rewrite_question(question, history)
    hits = await retrieve(db, search_query)
    if not hits:
        return EMPTY_STORE, []
    parts = []
    if history:
        parts.append(f"CONVERSATION:\n{_build_history(history)}")
    parts.append(f"CONTEXT:\n{_build_context(hits)}")
    parts.append(f"QUESTION: {question}")
    messages = [("system", SYSTEM_PROMPT), ("human", "\n\n".join(parts))]
    answer = (await get_llm().ainvoke(messages)).content
    if not isinstance(answer, str):
        answer = str(answer)
    sources = [chunk.chunk_id for chunk, _ in hits]
    logger.info("Q&A: %r -> %d sources", question[:80], len(sources))
    return answer.strip(), sources
