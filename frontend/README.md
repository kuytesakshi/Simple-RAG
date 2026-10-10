# Frontend (Next.js App Router)
Routes:
- `/login` - app/login/page.jsx
- `/chat` - app/chat/page.jsx (protected, redirects to /login without token)

Ports are env-tunable in `frontend/.env.local` (no root .env):
- `PORT` - Next.js dev port, default 3000
- `NEXT_PUBLIC_API_URL` - must match `BACKEND_PORT` in `backend/.env`, default http://localhost:8000

Run:
```
# .env.local already exists; or: cp .env.example .env.local
npm install
npm run dev
# http://localhost:3000
```
Backend URL via `NEXT_PUBLIC_API_URL` (default http://localhost:8000).
