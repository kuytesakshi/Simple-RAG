"""Prompt library service: versioned prompts in Postgres, cached in memory.

Rules:
- DEFAULTS below are the v1 seed only. Redeploys never overwrite DB content.
- Versions are append-only: set_prompt() inserts a new row ONLY when content
  differs from the active version (same text resubmitted -> no new version).
- Rollback re-points active_version; no rows are ever updated or deleted.
- chain.py reads via get_prompt() (in-memory, no per-turn queries).
  Call refresh_prompts() (or POST /api/prompts/reload) after edits.
"""
import logging
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prompt_library import Prompt, PromptVersion

logger = logging.getLogger(__name__)

REFUSAL = "I don't know based on the provided documents."

PROMPT_DEFAULTS: dict[str, str] = {
    "system": """You answer questions about the user's documents.
Rules:
1. Answer ONLY using the CONTEXT below. Never use outside knowledge.
2. The CONVERSATION is prior chat for understanding references (like "his" or
   "it"). It is NOT a source of facts — never quote it as evidence.
3. If the context does not contain the answer, reply with exactly: """
    + REFUSAL
    + """
4. Keep answers concise and factual.""",
    "rewrite": """Rewrite the follow-up question as a standalone question using the
conversation above. Rules: resolve pronouns/references from the conversation,
keep it to one sentence, output ONLY the rewritten question, never answer it.
If it is already standalone, repeat it unchanged.""",
    "classify": """Classify the user's latest message. Reply with exactly one word:
- "greeting" if it is a greeting, farewell, thanks, or other pleasantry
  (hi, hello, hey, thanks, thank you, bye, good morning...).
- "history" if it asks about the conversation itself (their previous
  questions, your previous answers, repeating or summarizing the chat).
- "off-scope" if it asks about something clearly unrelated to documents a
  person would chat about here AND unrelated to the conversation
  (world news, sports results, general trivia, coding help...).
- "documents" for anything else, including questions about the document topic
  and follow-ups referencing earlier turns ("his", "it", "that date"...).
Output only that one word, nothing else.

Examples:
"hi" -> greeting
"thanks a lot!" -> greeting
"what was my last question?" -> history
"summarize our chat so far" -> history
"what did I ask about before?" -> history
"who won the football world cup?" -> off-scope
"what is the name" -> documents
"what is the date of birth?" -> documents
"what is his college?" -> documents""",
    "expand": """Expand this short, vague question into one specific standalone
question so it can be searched in a document collection. Rules: resolve
pronouns ONLY from the conversation above; if no conversation is given, do
NOT mention any conversation — instead anchor toward the document (e.g. add
"in the document" or name the likely subject like "of the applicant").
Output ONLY the expanded question, never answer it.""",
    "greeting": """You are a friendly assistant for a document chatbot. Reply briefly and
warmly to the user's greeting or pleasantry (one or two sentences). Use the
conversation for tone if present. Do not claim document knowledge.""",
    "history": """You are replaying this conversation's transcript.
Rules:
1. Answer using ONLY the transcript below. Quote or summarize what was said.
2. If the transcript does not contain what is asked (e.g. no previous
   question exists), say you have no record of it in this conversation.
3. Do NOT invent turns that are not in the transcript.
4. Keep answers concise.""",
    "ambiguity": """Decide whether the question has ONE answer or SEVERAL distinct
answers in the evidence below. Rules: options must come ONLY from the
evidence, never invented; list at most 4 short options (a few words each).
Reply with exactly "SINGLE" if there is one answer. Otherwise reply with
"MULTIPLE" on the first line, then one option per line starting with "- ".
Examples:
Evidence names one applicant / Q "what is the applicant name?" -> SINGLE
Evidence names applicant, mother, director / Q "what is the name" ->
MULTIPLE
- Applicant: Sakshi Krushna Kuyte
- Mother: Jyoti
- Director: Dr. Mahesh Kakade""",
}

# name -> (active_version, content)
_cache: dict[str, tuple[int, str]] = {}


def get_prompt(name: str) -> str:
    """In-memory read. Falls back to DEFAULTS if cache is empty (e.g. tests)."""
    hit = _cache.get(name)
    if hit is not None:
        return hit[1]
    return PROMPT_DEFAULTS[name]


async def load_prompts(db: AsyncSession) -> int:
    """(Re)fill the cache from DB active versions. Returns prompt count."""
    _cache.clear()
    rows = (await db.execute(select(Prompt))).scalars().all()
    for p in rows:
        v = (
            await db.execute(
                select(PromptVersion).where(
                    PromptVersion.prompt_id == p.id,
                    PromptVersion.version == p.active_version,
                )
            )
        ).scalar_one_or_none()
        if v is not None:
            _cache[p.name] = (v.version, v.content)
    logger.info("Prompt cache loaded: %d prompts", len(_cache))
    return len(_cache)


async def refresh_prompts(db: AsyncSession) -> int:
    return await load_prompts(db)


async def seed_prompts(db: AsyncSession) -> int:
    """Insert v1 rows for missing names only. Returns rows created."""
    created = 0
    for name, content in PROMPT_DEFAULTS.items():
        existing = (
            await db.execute(select(Prompt).where(Prompt.name == name))
        ).scalar_one_or_none()
        if existing is not None:
            continue
        prompt = Prompt(name=name, active_version=1)
        db.add(prompt)
        await db.flush()
        db.add(PromptVersion(prompt_id=prompt.id, version=1, content=content, note="seed v1"))
        created += 1
    if created:
        await db.commit()
        logger.info("Seeded %d prompts at v1", created)
    return created


async def set_prompt(
    db: AsyncSession, name: str, content: str, note: str | None = None
) -> PromptVersion | None:
    """New version ONLY if content differs from active. Returns row or None."""
    prompt = (
        await db.execute(select(Prompt).where(Prompt.name == name))
    ).scalar_one_or_none()
    if prompt is None:
        raise ValueError(f"Unknown prompt: {name}")
    active = (
        await db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt.id,
                PromptVersion.version == prompt.active_version,
            )
        )
    ).scalar_one()
    if active.content == content:
        return None
    nxt = (
        await db.execute(
            select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt.id)
        )
    ).scalar_one() + 1
    row = PromptVersion(prompt_id=prompt.id, version=nxt, content=content, note=note)
    db.add(row)
    prompt.active_version = nxt
    await db.commit()
    await db.refresh(row)
    _cache[name] = (row.version, row.content)
    logger.info("Prompt %s bumped to v%d", name, nxt)
    return row


async def rollback_prompt(db: AsyncSession, name: str, version: int) -> PromptVersion:
    """Re-point active_version backward (or forward). No rows touched."""
    prompt = (
        await db.execute(select(Prompt).where(Prompt.name == name))
    ).scalar_one_or_none()
    if prompt is None:
        raise ValueError(f"Unknown prompt: {name}")
    target = (
        await db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt.id, PromptVersion.version == version
            )
        )
    ).scalar_one_or_none()
    if target is None:
        raise ValueError(f"Prompt {name} has no v{version}")
    prompt.active_version = version
    await db.commit()
    _cache[name] = (target.version, target.content)
    logger.info("Prompt %s rolled back to v%d", name, version)
    return target
