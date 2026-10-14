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
import re
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.rag.prompts import REFUSAL, get_prompt
from app.rag.vectorstore import retrieve

logger = logging.getLogger(__name__)

EMPTY_STORE = "No documents have been ingested yet. Run the ingestion script first."

# Reference markers: pronouns, demonstratives, continuations. Questions
# without them are standalone — feeding thread history to rewrite/expand
# can only poison them with unrelated topics (observed live).
_REFERENCE_RE = re.compile(
    r"\b(he|she|it|his|her|its|they|them|their|this|that|these|those|then|"
    r"same|previous|earlier|last|above|former|latter|other|another|more|"
    r"else|also|such)\b|^(and|but|so|or|nor)\b",
    re.IGNORECASE,
)


def _needs_context(question: str) -> bool:
    return bool(_REFERENCE_RE.search(question))

# Exact-match greetings skip the classifier LLM call entirely.
GREETING_WORDS = frozenset({
    "hi", "hii", "hiii", "hello", "hey", "hey!", "yo",
    "thanks", "thank you", "thankyou", "thx",
    "bye", "goodbye", "good morning", "good afternoon", "good evening",
})


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
    import re

    # Exact greetings skip the LLM call: deterministic + free.
    normalized = re.sub(r"[!?.\s]+$", "", question.strip().lower())
    if normalized in GREETING_WORDS:
        logger.info("Classify: %r -> greeting (shortcut)", question[:80])
        return "greeting"
    parts = []
    if history:
        parts.append(f"CONVERSATION:\n{_build_history(history)}")
    parts.append(f"MESSAGE: {question}")
    verdict = await _llm_text([("system", get_prompt("classify")), ("human", "\n\n".join(parts))])
    verdict = verdict.lower().strip().strip('"')
    route = verdict if verdict in ("greeting", "history", "documents", "off-scope") else "documents"
    logger.info("Classify: %r -> %s", question[:80], route)
    return route


async def rewrite_question(question: str, history: list[tuple[str, str]]) -> str:
    """Follow-up -> standalone query. Skipped when nothing needs resolving.

    Skip cases (no LLM call): no history, or no reference markers in the
    question. Without markers the question is standalone — rewriting can only
    poison it by merging unrelated thread topics (observed live).
    """
    if not history or not _needs_context(question):
        logger.info("Rewrite skipped (standalone): %r", question[:80])
        return question
    rewritten = await _llm_text(
        [
            (
                "human",
                f"CONVERSATION:\n{_build_history(history)}\n\n{get_prompt('rewrite')}\n\nFOLLOW-UP: {question}",
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
    return await _llm_text([("system", get_prompt("greeting")), ("human", "\n\n".join(parts))]), []


async def answer_from_history(
    question: str, history: list[tuple[str, str]]
) -> tuple[str, list[str]]:
    """Answer about the dialogue itself. No document sources apply."""
    answer = await _llm_text(
        [
            ("system", get_prompt("history")),
            ("human", f"TRANSCRIPT:\n{_build_history(history)}\n\nQUESTION: {question}"),
        ]
    )
    logger.info("History Q&A: %r", question[:80])
    return answer, []


async def expand_query(question: str, history: list[tuple[str, str]]) -> str:
    """Vague question -> specific searchable form (used only on weak hits)."""
    parts = []
    if history:
        parts.append(f"CONVERSATION:\n{_build_history(history)}")
    parts.append(f"{get_prompt('expand')}\n\nQUESTION: {question}")
    expanded = await _llm_text([("human", "\n\n".join(parts))])
    expanded = expanded.strip().strip('"')
    logger.info("Expand: %r -> %r", question[:80], expanded[:120])
    return expanded or question


async def check_ambiguity(
    question: str, hits
) -> tuple[bool, list[str]]:
    """Does the evidence hold several distinct answers? Returns (flag, options).

    Runs only on retrieved hits (no extra cost on other branches). Options
    come strictly from chunk text — the prompt forbids inventing any.
    """
    if not settings.AMBIGUITY_CHECK or len(hits) < 2:
        return False, []
    evidence = "\n\n".join(f"- {chunk.content[:500]}" for chunk, _ in hits)
    verdict = await _llm_text(
        [
            ("system", get_prompt("ambiguity")),
            ("human", f"EVIDENCE:\n{evidence}\n\nQUESTION: {question}"),
        ]
    )
    lines = [ln.strip() for ln in verdict.splitlines() if ln.strip()]
    if not lines or lines[0].upper() != "MULTIPLE":
        return False, []
    options = [
        ln.lstrip("-•0123456789. ").strip() for ln in lines[1:4]
    ]
    options = [o for o in options if o]
    if not options:
        return False, []
    logger.info("Ambiguous: %r -> %d options", question[:80], len(options))
    return True, options


async def answer_from_documents(
    db: AsyncSession, question: str, history: list[tuple[str, str]]
) -> tuple[str, list[str]]:
    search_query = await rewrite_question(question, history)
    hits = await retrieve(db, search_query)
    if not hits:
        return EMPTY_STORE, []
    # Weak best hit (vague wording landed in the wrong neighborhood):
    # expand once and re-retrieve instead of answering from bad context.
    # Expansion gets thread history ONLY for marker-bearing questions;
    # otherwise it would import unrelated topics (observed live).
    if hits[0][1] > settings.RETRIEVAL_MAX_DISTANCE:
        logger.info(
            "Weak hit (dist=%.4f), expanding: %r", hits[0][1], question[:80]
        )
        ctx = history if _needs_context(question) else []
        hits = await retrieve(db, await expand_query(question, ctx))
        if not hits:
            return EMPTY_STORE, []
    ambiguous, options = await check_ambiguity(question, hits)
    if ambiguous:
        numbered = "\n".join(f"{i}. {o}" for i, o in enumerate(options, 1))
        return (
            f"I found several possible answers — which one do you mean?\n{numbered}",
            [chunk.chunk_id for chunk, _ in hits],
        )
    parts = []
    if history:
        parts.append(f"CONVERSATION:\n{_build_history(history)}")
    parts.append(f"CONTEXT:\n{_build_context(hits)}")
    parts.append(f"QUESTION: {question}")
    messages = [("system", get_prompt("system")), ("human", "\n\n".join(parts))]
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
