from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api.routes import auth, chat, conversations, ingest, prompts
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models import user as _user_model  # noqa: F401  (registers users table)
from app.models import document as _document_model  # noqa: F401  (registers RAG tables)
from app.models import conversation as _conversation_model  # noqa: F401  (registers chat history)
from app.models import prompt_library as _prompt_model  # noqa: F401  (registers prompt library)

# App loggers (app.rag.* route/rewrite/expand evidence) visible in docker logs.
# Explicit handler: uvicorn's root config filters our INFO records otherwise.
_app_log = logging.getLogger("app")
_app_log.setLevel(logging.INFO)
if not _app_log.handlers:
    _app_log.addHandler(logging.StreamHandler())

# Create tables on startup (simple dev approach; use Alembic later)
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Enable pgvector extension
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Backfill for pre-existing DBs: create_all never ALTERs tables
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
        await conn.run_sync(Base.metadata.create_all)
    # Prompt library: seed v1 rows for missing names, then fill memory cache
    from app.rag import prompts as prompt_service
    async with SessionLocal() as db:
        await prompt_service.seed_prompts(db)
        await prompt_service.load_prompts(db)
    yield

app = FastAPI(title="Simple RAG Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
