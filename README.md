# Simple RAG

PDF in `backend/Data/` -> Backend (FastAPI + Postgres pgvector + Groq) -> Frontend (Next.js login + chatbot).

## Structure (no root .env)
```
docker-compose.yml     # db (pgvector/pgvector:pg16) + backend (Dockerfile-driven)
backend/
  .env                 # backend secrets + port tuning: GROQ_*, DATABASE_URL, JWT_SECRET, POSTGRES_*, BACKEND_PORT
  Data/                # your PDFs (mounted read-only to /app/Data in Docker)
  Dockerfile           # whole backend driven by this
  requirements.txt
  app/
    main.py            # FastAPI entry
    core/              # config, database, security (JWT)
    api/routes/        # auth, chat, ingest
    rag/               # loader, chunker, embeddings, vectorstore, chain
    models/            # pydantic schemas
  scripts/ingest_data.py
frontend/ (Next.js App Router)
  app/                 # layout.jsx, page.jsx (-> /chat), login/page.jsx, chat/page.jsx
  components/          # ChatWindow.jsx, MessageBubble.jsx
  context/             # AuthContext.jsx (JWT, client component)
  lib/api.js           # axios with token, uses NEXT_PUBLIC_API_URL
```

## Ports (all env-tunable, no combined env)
| Service  | Tuned in | Var | Container/app port | Default URL |
|----------|----------|-----|--------------------|-------------|
| backend  | `backend/.env` | `BACKEND_PORT` | 8000 | http://localhost:8000/docs |
| postgres | `backend/.env` | `POSTGRES_PORT` | 5432 | localhost:5432 |
| frontend | `frontend/.env.local` | `PORT` | 3000 | http://localhost:3000 |

If you change `BACKEND_PORT` in `backend/.env`, also update `NEXT_PUBLIC_API_URL=http://localhost:<BACKEND_PORT>` in `frontend/.env.local`.

## Run backend (Docker)
```
# backend/.env is the interpolation file + container env_file
docker compose --env-file backend/.env up --build
# API docs: http://localhost:8000/docs (or your BACKEND_PORT)
# Ingest PDFs: docker compose --env-file backend/.env exec backend python scripts/ingest_data.py
```

## Run frontend (Next.js)
```
cd frontend
# .env.local already exists with PORT + NEXT_PUBLIC_API_URL; edit as needed
npm install
npm run dev
# http://localhost:3000  login -> /chat
```
