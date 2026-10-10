"""Step 1 verification: load Data/*.pdf and report what was found.

Run inside docker:
    docker compose --env-file backend/.env exec backend python scripts/ingest_data.py
(Later steps will add: chunk -> embed -> upsert into pgvector.)
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo-root on sys.path

from app.rag.loader import discover_pdfs, load_documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    pdfs = discover_pdfs()
    print(f"PDFs found: {[p.name for p in pdfs]}")
    docs = load_documents()
    print(f"Total page-documents: {len(docs)}")
    if docs:
        first = docs[0]
        print(f"Sample -> source={first.metadata.get('source')} page={first.metadata.get('page')}")
        print(f"Sample text (first 300 chars): {first.page_content[:300]!r}")
