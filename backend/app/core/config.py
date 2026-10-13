from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    DATABASE_URL: str = "postgresql+psycopg://raguser:ragpass@localhost:5432/ragdb"
    DATA_DIR: str = "/app/Data"
    JWT_SECRET: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    # Frontend origin allowed to call this API (browser CORS).
    FRONTEND_URL: str = "http://localhost:3000"
    # RAG chunking (step 2)
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    # RAG retrieval: how many chunks per query (env only, no per-request override)
    RETRIEVAL_TOP_K: int = 4
    # RAG retrieval: best-hit distance above this triggers expand-and-retry
    # (measured: good hits ~0.55, vague misses ~0.80+)
    RETRIEVAL_MAX_DISTANCE: float = 0.70
    # RAG chat: how many prior messages of THIS conversation feed the LLM
    CHAT_HISTORY_TURNS: int = 6

    class Config:
        # Locally: backend/.env | In Docker: /app/.env (copied from backend/.env)
        env_file = ".env"
        extra = "ignore"

settings = Settings()
