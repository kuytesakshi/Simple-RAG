"""Final RAG step: classify -> route -> answer (Groq LLM).

Every turn is classified into exactly one route:
- greeting: conversational reply (hi/thanks/bye), history for tone, no retrieval.
- history:  question about the dialogue itself -> answered from the transcript.
             Quoting what was said is not hallucination.
- documents: rewrite follow-up -> retrieve top-k -> strict grounding answer.
             Only document CONTEXT is evidence; conversation is context only.
- off-scope: instant refusal, no retrieval or answer calls spent.

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

CLASSIFY_PROMPT = """Classify the user's latest message. Reply with exactly one word:
- "greeting" if it is a greeting, farewell, thanks, or other pleasantry
  (hi, hello, hey, thanks, thank you, bye, good morning...).
- "history" if it asks about the conversation itself (their previous
  questions, your previous answers, repeating or summarizing the chat).
- "off-scope" if it asks about something clearly unrelated to documents a
  person would chat about here AND unrelated to the conversation
  (world news, sports results, general trivia, coding help...).
- "documents" for anything else, including questions about the document topic
  and follow-ups referencing earlier turns ("his", "it", "that date"...).
Output only that one word, nothing else."""

GREETING_PROMPT = """You are a friendly assistant for a document chatbot. Reply briefly and
warmly to the user's greeting or pleasantry (one or two sentences). Use the
conversation for tone if present. Do not claim document knowledge."""

HISTORY_PROMPT = """You are replaying this conversation's transcript.
Rules:
1. Answer using ONLY the transcript below. Quote or summarize what was said.
2. If the transcript does not contain what is asked (e.g. no previous
   question exists), say you have no record of it in this conversation.
3. Do NOT invent turns that are not in the transcript.
4. Keep answers concise."""


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


async def _llm_text(messages) -> str:
    out = (await get_llm().ainvoke(messages)).content
    if not isinstance(out, str):
        out = str(out)
    return out.strip()


async def classify_question(question: str, history: list[tuple[str, str]]) -> str:
    """One of greeting/history/documents/off-scope. Safe default: documents."""
    parts = []
    if history:
        parts.append(f"CONVERSATION:\n{_build_history(history)}")
    parts.append(f"MESSAGE: {question}")
    verdict = await _llm_text([("system", CLASSIFY_PROMPT), ("human", "\n\n".join(parts))])
    verdict = verdict.lower().strip().strip('"')
    route = verdict if verdict in ("greeting", "history", "documents", "off-scope") else "documents"
    logger.info("Classify: %r -> %s", question[:80], route)
    return route


async def rewrite_question(question: str, history: list[tuple[str, str]]) -> str:
    """Follow-up -> standalone query. Skipped (no LLM call) when no history."""
    if not history:
        return question
    rewritten = await _llm_text(
        [
            (
                "human",
                f"CONVERSATION:\n{_build_history(history)}\n\n{REWRITE_PROMPT}\n\nFOLLOW-UP: {question}",
            )
        ]
    )
    rewritten = rewritten.strip().strip('"')
    logger.info("Rewrite: %r -> %r", question[:80], rewritten[:120])
    return rewritten or question


async def answer_greeting(question: str, history: list[tuple[str, str]]) -> tuple[str, list[str]]:
    parts = []
    if history:
        parts.append(f"CONVERSATION:\n{_build_history(history)}")
    parts.append(f"MESSAGE: {question}")
    return await _llm_text([("system", GREETING_PROMPT), ("human", "\n\n".join(parts))]), []


async def answer_from_history(
    question: str, history: list[tuple[str, str]]
) -> tuple[str, list[str]]:
    """Answer about the dialogue itself. No document sources apply."""
    answer = await _llm_text(
        [
            ("system", HISTORY_PROMPT),
            ("human", f"TRANSCRIPT:\n{_build_history(history)}\n\nQUESTION: {question}"),
        ]
    )
    logger.info("History Q&A: %r", question[:80])
    return answer, []


async def answer_from_documents(
    db: AsyncSession, question: str, history: list[tuple[str, str]]
) -> tuple[str, list[str]]:
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
    answer = await _llm_text(messages)
    sources = [chunk.chunk_id for chunk, _ in hits]
    logger.info("Q&A: %r -> %d sources", question[:80], len(sources))
    return answer, sources


async def answer_question(
    db: AsyncSession,
    question: str,
    history: list[tuple[str, str]] | None = None,
) -> tuple[str, list[str]]:
    """Classify once, then run exactly one branch. Returns (answer, sources)."""
    history = history or []
    route = await classify_question(question, history)
    if route == "greeting":
        return await answer_greeting(question, history)
    if route == "history":
        return await answer_from_history(question, history)
    if route == "off-scope":
        logger.info("Off-scope refusal: %r", question[:80])
        return REFUSAL, []
    return await answer_from_documents(db, question, history)
