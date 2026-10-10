"""Step 2 verification: load Data/*.pdf -> chunk -> report stats.

Run inside docker:
    docker compose --env-file backend/.env exec backend python scripts/ingest_data.py
(Later steps will add: embed -> upsert into pgvector.)
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo-root on sys.path

from app.rag.chunker import split_documents
from app.rag.loader import discover_pdfs, load_documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    pdfs = discover_pdfs()
    print(f"PDFs found: {[p.name for p in pdfs]}")
    docs = load_documents()
    print(f"Total page-documents: {len(docs)}")
    chunks = split_documents(docs)
    print(f"Total chunks: {len(chunks)}")
    if chunks:
        sizes = [len(c.page_content) for c in chunks]
        print(f"Chunk chars: min={min(sizes)} avg={sum(sizes)//len(sizes)} max={max(sizes)}")
        first = chunks[0]
        print(f"Sample -> chunk_id={first.metadata.get('chunk_id')}")
        print(f"Sample text (first 300 chars): {first.page_content[:300]!r}")
