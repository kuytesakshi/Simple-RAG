"""Storage + retrieval over document_chunks (pgvector, cosine distance).

Hybrid mode (default): dense cosine + BM25 keyword legs fused with
Reciprocal Rank Fusion. Same [(chunk, cosine_distance)] return shape either
way, so callers (tripwire, sources) work unchanged.
"""
import logging
import re
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document as LCDocument
from rank_bm25 import BM25Okapi
from app.core.config import settings
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)

# Full-scan cap for the dense leg in hybrid mode (exact scan is full-table
# anyway today; revisit with ANN/prefilter if chunks grow 100x).
_MAX_SCAN = 1000


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


# Stopwords dilute BM25 (every chunk matches what/is/the); drop them so
# rare content tokens decide. NOTE: "be" is deliberately KEPT ("B.E." degree).
_STOPWORDS = frozenset(
    "what is the in and of a an to for on with from by are was were been "
    "or as at it this that these those there here how when where which who "
    "whom whose do does did done have has had having can could should would "
    "will shall may might must my your his her its our their mine yours hers "
    "ours theirs me him us them you we they he she it this s t re ve ll d m".split()
)

# Domain synonyms, expanded symmetrically on query AND corpus tokens so both
# sides share vocabulary ("semester" <-> "sem", "result" <-> "marks"...).
_SYNONYMS = {
    "semester": ["sem"], "semesters": ["sem"], "sem": ["semester"],
    "result": ["marks", "grades"], "results": ["marks", "grades"],
    "marks": ["result"], "grades": ["result"], "mark": ["result"], "grade": ["result"],
    "percentage": ["marks", "percent"], "percent": ["marks"],
    "first": ["fe", "1"], "second": ["se", "2"], "third": ["te", "3"],
    "be": ["fe", "se"], "bachelor": ["be"],
    "college": ["institute", "school"], "university": ["institute"],
    "name": ["names"], "names": ["name"],
}


def _normalize_tokens(tokens: list[str]) -> list[str]:
    kept = [t for t in tokens if t not in _STOPWORDS]
    expanded = list(kept)
    for t in kept:
        expanded.extend(_SYNONYMS.get(t, []))
    return expanded


async def upsert_document(
    db: AsyncSession,
    *,
    filename: str,
    page_count: int,
    chunks: list[LCDocument],
    vectors: list[list[float]],
) -> Document:
    """Delete-by-source + re-insert: wipe this file's rows, insert fresh.

    Bulk deletes (no relationship lazy-loads: those break under asyncio).
    """
    old = (
        await db.execute(select(Document).where(Document.filename == filename))
    ).scalar_one_or_none()
    if old is not None:
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == old.id))
        await db.execute(delete(Document).where(Document.id == old.id))
        await db.flush()
        logger.info("Cleared %s previous rows for %s", "stale", filename)

    doc = Document(
        filename=filename, page_count=page_count,
        chunk_count=len(chunks), status="ingested",
    )
    db.add(doc)
    await db.flush()  # assigns doc.id
    for ch, vec in zip(chunks, vectors):
        db.add(
            DocumentChunk(
                document_id=doc.id,
                content=ch.page_content,
                embedding=vec,
                source=ch.metadata.get("source", filename),
                page=int(ch.metadata.get("page", 0)),
                chunk_id=ch.metadata["chunk_id"],
            )
        )
    await db.commit()
    await db.refresh(doc)
    logger.info("Upserted %s: %d chunks", filename, len(chunks))
    return doc


async def similarity_search(
    db: AsyncSession, query_vector: list[float], k: int | None = None
) -> list[tuple[DocumentChunk, float]]:
    """Top-k chunks by cosine distance (no HNSW index yet: exact scan).

    k=None -> live settings.RETRIEVAL_TOP_K, so tuning backend/.env needs
    only a restart, no code change.
    """
    k = settings.RETRIEVAL_TOP_K if k is None else k
    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    rows = (
        await db.execute(
            select(DocumentChunk, distance).order_by("distance").limit(k)
        )
    ).all()
    return [(chunk, dist) for chunk, dist in rows]


async def retrieve(
    db: AsyncSession, query_text: str, k: int | None = None
) -> list[tuple[DocumentChunk, float]]:
    """End-to-end retrieval: hybrid (RRF) by default, pure vector if disabled."""
    from app.rag.embeddings import embed_query  # lazy: avoids import cycle

    k = settings.RETRIEVAL_TOP_K if k is None else k
    query_vector = embed_query(query_text)
    if not settings.RETRIEVAL_HYBRID:
        return await similarity_search(db, query_vector, k=k)

    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    rows = (
        await db.execute(
            select(DocumentChunk, distance).order_by("distance").limit(_MAX_SCAN)
        )
    ).all()
    if not rows:
        return []
    chunks = [chunk for chunk, _ in rows]
    cos_by_id = {chunk.id: dist for chunk, dist in rows}

    bm25 = BM25Okapi([_normalize_tokens(_tokenize(ch.content)) for ch in chunks])
    bm25_scores = bm25.get_scores(_normalize_tokens(_tokenize(query_text)))
    # Only chunks sharing at least one query token take part in fusion.
    order = sorted(range(len(chunks)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_rank = {chunks[i].id: rank for rank, i in enumerate(order) if bm25_scores[i] > 0}

    rrf_k = settings.RRF_K
    dense_w, bm25_w = settings.DENSE_WEIGHT, settings.BM25_WEIGHT
    fused: dict = {}
    for rank, (chunk, _) in enumerate(rows):
        fused[chunk.id] = fused.get(chunk.id, 0.0) + dense_w / (rrf_k + rank + 1)
    for cid, rank in bm25_rank.items():
        fused[cid] = fused.get(cid, 0.0) + bm25_w / (rrf_k + rank + 1)
    by_id = {chunk.id: chunk for chunk, _ in rows}
    top = sorted(fused, key=lambda cid: fused[cid], reverse=True)[:k]
    logger.info(
        "Hybrid retrieve: %d candidates -> top %d (rrf_k=%d, dense_w=%.1f, bm25_w=%.1f)",
        len(rows), len(top), rrf_k, dense_w, bm25_w,
    )
    return [(by_id[cid], cos_by_id[cid]) for cid in top]
