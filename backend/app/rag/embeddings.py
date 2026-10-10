"""Step 3 of the RAG pipeline: free local embeddings.

all-MiniLM-L6-v2 -> 384 dims. The model weights are baked into the Docker
image, so no download happens at runtime. Changing the model requires a
migration (Vector dim) + full re-embed, so the name lives here as a constant.
"""
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBED_BATCH_SIZE = 32


@lru_cache(maxsize=1)
def get_embeddings():
    """Singleton: model loads once (~100MB), then stays in memory."""
    from langchain_huggingface import HuggingFaceEmbeddings  # lazy: keeps API startup light

    model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    dim = len(model.embed_query("dim probe"))
    if dim != EMBEDDING_DIM:
        raise ValueError(f"Model dim {dim} != Vector({EMBEDDING_DIM}) column — migrate first")
    logger.info("Embedding model ready: %s (%d dims)", EMBEDDING_MODEL, dim)
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of chunk texts -> list of vectors."""
    return get_embeddings().embed_documents(texts)


def embed_query(text: str) -> list[float]:
    return get_embeddings().embed_query(text)
