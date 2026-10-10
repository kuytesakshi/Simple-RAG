FROM python:3.11-slim

WORKDIR /app

# Slow-network friendly + HuggingFace cache locations (baked into image layer)
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10 \
    HF_HOME=/opt/hf-cache \
    HF_HUB_CACHE=/opt/hf-cache/hub \
    TRANSFORMERS_CACHE=/opt/hf-cache/hub \
    SENTENCE_TRANSFORMERS_HOME=/opt/hf-cache/sentence-transformers

# system deps for pgvector/psycopg + pdf parsing (apt lists cached by BuildKit)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 1. CPU-only torch first: avoids ~2GB NVIDIA CUDA wheels.
#    sentence-transformers later reuses this instead of downloading CUDA torch.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://download.pytorch.org/whl/cpu torch

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 2. Pre-download free embedding model into the image layer,
#    so first query is fast and rebuilds reuse this layer when Dockerfile/requirements are unchanged.
ARG EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
