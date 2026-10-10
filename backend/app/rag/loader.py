"""Step 1 of the RAG pipeline: load PDFs from DATA_DIR into LangChain Documents.

Each PDF page becomes one Document (via LangChain's PyPDFLoader, powered by
pypdf). Metadata per page: {"source": "<filename>", "page": <0-based int>}.
"""
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.config import settings

logger = logging.getLogger(__name__)

DATA_GLOB = "*.pdf"


def discover_pdfs(data_dir: str | Path | None = None) -> list[Path]:
    """Return sorted PDF paths in DATA_DIR (empty list if dir missing)."""
    base = Path(data_dir or settings.DATA_DIR)
    if not base.is_dir():
        logger.warning("DATA_DIR %s does not exist or is not a directory", base)
        return []
    # sorted() keeps ingestion deterministic across runs
    return sorted(base.glob(DATA_GLOB))


def load_documents(data_dir: str | Path | None = None) -> list[Document]:
    """Load every PDF in DATA_DIR; one bad file never kills the whole run."""
    docs: list[Document] = []
    for pdf in discover_pdfs(data_dir):
        try:
            pages = PyPDFLoader(str(pdf)).load()
        except Exception:
            logger.exception("Skipping unreadable PDF: %s", pdf.name)
            continue
        # Drop blank pages (scanned/empty) so they don't pollute retrieval
        pages = [p for p in pages if p.page_content.strip()]
        for p in pages:
            # Normalize to filename (PyPDFLoader puts the full path here)
            p.metadata["source"] = pdf.name
        logger.info("Loaded %s: %d pages", pdf.name, len(pages))
        docs.extend(pages)
    logger.info("Total: %d page-documents from %s", len(docs), data_dir or settings.DATA_DIR)
    return docs
