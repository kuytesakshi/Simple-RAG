"""Storage + retrieval over document_chunks (pgvector, cosine distance)."""
import logging
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document as LCDocument
from app.core.config import settings
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


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
    """End-to-end retrieval: embed query text -> top-k chunks, best first."""
    from app.rag.embeddings import embed_query  # lazy: avoids import cycle

    return await similarity_search(db, embed_query(query_text), k=k)
