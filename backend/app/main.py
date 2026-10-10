from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, chat, ingest
from app.core.config import settings
from app.core.database import engine, Base
from app.models import user as _user_model  # noqa: F401  (registers users table)
from app.models import document as _document_model  # noqa: F401  (registers RAG tables)

# Create tables on startup (simple dev approach; use Alembic later)
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Enable pgvector extension
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
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
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
