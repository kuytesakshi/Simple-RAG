"""Step 2 of the RAG pipeline: split page-documents into retrieval chunks.

Uses RecursiveCharacterTextSplitter: tries paragraph breaks first, then lines,
then words — so chunks keep whole sentences together when possible.
Overlap preserves context across chunk boundaries (answers spanning a split
are still retrievable).
"""
import logging
from collections import Counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)

# Defaults come from env (backend/.env); import-time snapshot for back-compat.
CHUNK_SIZE = settings.CHUNK_SIZE
CHUNK_OVERLAP = settings.CHUNK_OVERLAP


def get_splitter(chunk_size: int | None = None, chunk_overlap: int | None = None):
    # None -> live env value, so tuning backend/.env needs only a restart, no code change
    chunk_size = settings.CHUNK_SIZE if chunk_size is None else chunk_size
    chunk_overlap = settings.CHUNK_OVERLAP if chunk_overlap is None else chunk_overlap
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
    )


def split_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split pages into chunks; stamps each with a stable chunk_id.

    chunk_id = "<source>:p<page>:c<n>" (n = ordinal within that page),
    so retrieved chunks can cite exact file + page later.
    """
    splitter = get_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_documents(docs)
    seen: Counter[tuple] = Counter()
    for ch in chunks:
        key = (ch.metadata.get("source"), ch.metadata.get("page"))
        ch.metadata["chunk_id"] = f"{key[0]}:p{key[1]}:c{seen[key]}"
        seen[key] += 1
    logger.info(
        "Split %d pages -> %d chunks (size=%d, overlap=%d)",
        len(docs), len(chunks), chunk_size, chunk_overlap,
    )
    return chunks
