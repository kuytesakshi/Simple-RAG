"""Full local ingestion: load -> chunk -> embed -> upsert into pgvector.

Run inside docker:
    docker compose --env-file backend/.env exec backend python scripts/ingest_data.py
"""
import asyncio
import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo-root on sys.path

from app.core.database import SessionLocal
from app.rag.chunker import split_documents
from app.rag.embeddings import EMBED_BATCH_SIZE, embed_query, embed_texts
from app.rag.loader import discover_pdfs, load_documents
from app.rag.vectorstore import similarity_search, upsert_document

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SAMPLE_QUERY = "What is the applicant's college and name?"


async def main() -> None:
    pdfs = discover_pdfs()
    print(f"PDFs found: {[p.name for p in pdfs]}")
    docs = load_documents()
    chunks = split_documents(docs)
    print(f"Total page-documents: {len(docs)}, chunks: {len(chunks)}")
    if not chunks:
        print("Nothing to ingest.")
        return

    # Embed in bounded batches (keeps memory flat as Data/ grows)
    vectors: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = [c.page_content for c in chunks[i : i + EMBED_BATCH_SIZE]]
        vectors.extend(embed_texts(batch))
        print(f"Embedded {min(i + EMBED_BATCH_SIZE, len(chunks))}/{len(chunks)}")
    print(f"Vector dim: {len(vectors[0])}")

    # Group by file so each parent documents row gets true page/chunk counts
    by_file: dict[str, list] = defaultdict(list)
    pages_per_file: dict[str, set] = defaultdict(set)
    for ch in chunks:
        src = ch.metadata.get("source", "unknown")
        by_file[src].append(ch)
        pages_per_file[src].add(ch.metadata.get("page"))
    order = {ch.metadata["chunk_id"]: v for ch, v in zip(chunks, vectors)}

    async with SessionLocal() as db:
        for filename, file_chunks in by_file.items():
            file_vectors = [order[ch.metadata["chunk_id"]] for ch in file_chunks]
            doc = await upsert_document(
                db, filename=filename,
                page_count=len(pages_per_file[filename]),
                chunks=file_chunks, vectors=file_vectors,
            )
            print(f"Upserted {doc.filename}: pages={doc.page_count} chunks={doc.chunk_count}")

        # Prove retrieval works: sample cosine query over what we just stored
        qvec = embed_query(SAMPLE_QUERY)
        hits = await similarity_search(db, qvec, k=2)
        print(f"Sample query: {SAMPLE_QUERY!r}")
        for chunk, dist in hits:
            print(f"  dist={dist:.4f} {chunk.chunk_id} :: {chunk.content[:120]!r}")


if __name__ == "__main__":
    asyncio.run(main())
