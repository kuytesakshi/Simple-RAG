# Backend (FastAPI + pgvector + Groq)
Env in `backend/.env` (GROQ_API_KEY, DATABASE_URL, JWT_SECRET + POSTGRES_* + BACKEND_PORT port tuning).
PDFs in `backend/Data/` -> mounted to `/app/Data` in Docker.

Run via Docker from repo root:
```
docker compose --env-file backend/.env up --build
```
API: http://localhost:8000/docs (host port = BACKEND_PORT in backend/.env)
