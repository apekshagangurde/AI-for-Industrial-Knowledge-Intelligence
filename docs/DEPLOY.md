# Deploy Runbook (#35)

Goal: a live public URL as a demo backup, not just localhost. Configs are in the
repo (`backend/Dockerfile`, `render.yaml`, `frontend/vercel.json`); this is the
click-path plus the fast fallback.

## Backend → Render (Docker, free tier)

1. Push this branch to GitHub.
2. Render dashboard → **New → Blueprint** → select this repo. It reads
   `render.yaml` and creates the `iki-backend` web service.
3. Set secrets (dashboard → service → Environment): `GROQ_API_KEY`, and
   `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`.
4. **Neo4j**: the local Docker Neo4j isn't reachable from Render. Create a free
   **Neo4j Aura** instance (neo4j.com/cloud/aura-free), then run the graph
   writer against it once from your laptop with the Aura creds in `.env`:
   `python -m ingestion.graph_writer`. Put the Aura bolt URI + creds into
   Render's env. Without this, chat/RCA/compliance/lessons still work; only the
   Graph tab and KG-expansion boost are degraded.
5. The Docker build bakes the Chroma index (`embed_store` runs at build time),
   so the service answers immediately on boot — no persistent disk needed.
6. Confirm: `curl https://<service>.onrender.com/health` → `{"status":"ok"}`.

## Frontend → Vercel

1. Vercel → **New Project** → import the repo → set **Root Directory** to
   `frontend/`. `vercel.json` handles the Vite build.
2. Env var: `VITE_API_BASE_URL = https://<service>.onrender.com`.
3. Deploy. Open the Vercel URL, ask a P-101 question, confirm cited answer.

## Fast fallback (if a deploy is flaky under time pressure)

Run both locally and expose the backend with a tunnel:

```bash
# terminal 1
cd backend && source .venv/bin/activate && uvicorn main:app --port 8000
# terminal 2 — public URL for the backend
ngrok http 8000
# terminal 3 — point the frontend at the ngrok URL, then run it
cd frontend && VITE_API_BASE_URL=https://<id>.ngrok-free.app pnpm dev
```

Vercel for the frontend + ngrok for the backend is the most reliable
demo-day combination when free-tier backends are slow to cold-start.

## Free-tier gotchas

- Render free web services **cold-start** (~30-60s after idle). Hit `/health`
  a few minutes before the demo to warm it.
- Groq free tier caps at **100k tokens/day** shared across the whole app. For a
  live demo, keep a spare `GROQ_API_KEY`, or set `ENTITY_BACKEND=gliner` (already
  the default) so ingestion doesn't burn chat's budget.
