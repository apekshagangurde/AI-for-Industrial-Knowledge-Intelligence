# AI for Industrial Knowledge Intelligence

An AI-powered platform that ingests heterogeneous industrial documents (engineering drawings,
maintenance records, safety procedures, inspection reports, operating instructions) and makes
their collective intelligence queryable via a knowledge-graph-aware RAG copilot — plus thin
agentic slices for compliance checking, root-cause analysis, and lessons-learned alerts.

Flagship feature: **Expert Knowledge Copilot** (RAG + Knowledge Graph fusion, with citations and
confidence scores). See open [Issues](../../issues) for the full build breakdown, grouped by
`track:*` labels.

## Project Structure

```
.
├── backend/          # Python: ingestion, RAG, knowledge graph, API (FastAPI)
├── frontend/          # React + TypeScript + Tailwind chat UI (scaffolded in issue #21)
├── data/
│   ├── raw/           # Public seed documents (OSHA, PESO/OISD, sample P&IDs) — issue #3
│   ├── synthetic/      # Generated "Plant Alpha" dataset — issue #4
│   └── processed/      # Pipeline output (parsed/chunked docs) — gitignored
├── scripts/           # One-off setup/utility scripts (KG constraints, smoke tests)
├── docs/              # Architecture notes, KG schema, demo script/slides
├── docker-compose.yml  # Local Neo4j + Chroma — issue #2
├── .env.example        # Required environment variables (copy to .env)
└── README.md
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running, not just installed)
- Python 3.10+ — on macOS, don't rely on whatever `python3` resolves to first. The Python 3.9
  bundled with Xcode Command Line Tools is too old for some deps (`pip install` fails compiling
  `olefile` with a `SyntaxError`). Check `python3 --version`; if it's not 3.10+, point the venv at
  a real interpreter, e.g. `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` or a
  Homebrew Python.
- Node.js 18+ and pnpm (`npm install -g pnpm` if you don't have it)
- A free [Groq API key](https://console.groq.com) (console.groq.com → API Keys → Create API Key)
  — takes about a minute, no credit card. Local [Ollama](https://ollama.com) works as an offline
  fallback if you'd rather not sign up for anything.
- Tesseract OCR binary (needed for #8's OCR pipeline) — `pip install pytesseract` only installs
  the Python wrapper, not the OCR engine itself: `brew install tesseract` on macOS, `apt install
  tesseract-ocr` on Debian/Ubuntu.

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/apekshagangurde/AI-for-Industrial-Knowledge-Intelligence.git
cd AI-for-Industrial-Knowledge-Intelligence

# 2. Configure environment
cp .env.example .env
# open .env and paste your GROQ_API_KEY (or set up Ollama — see .env.example comments)
# API_PORT defaults to 8000. If something else on your machine already owns 8000 (another
# local project, a different Docker container, etc.), change API_PORT and VITE_API_BASE_URL
# in .env to a free port, e.g. 8001 — see Troubleshooting.

# 3. Start local infra (Neo4j knowledge graph)
docker compose up -d

# 4. Backend — Python virtual env + dependencies (use a real Python 3.10+, see Prerequisites)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4a. Build the vector index — required once (and after any change to data/raw
# or data/synthetic) before /query can return anything grounded. Downloads the
# bge-small-en-v1.5 embedding model on first run.
python -m ingestion.embed_store

uvicorn main:app --host 0.0.0.0 --port "${API_PORT:-8000}" --reload
cd ..

# 5. Frontend (separate terminal)
cd frontend
pnpm install
pnpm run dev
```

### Verify your setup

- **Neo4j:** `docker ps --filter name=industrial-ki-neo4j` should show `Up ... (healthy)`.
  Open [http://localhost:7474](http://localhost:7474) and log in with the `NEO4J_USER` /
  `NEO4J_PASSWORD` from your `.env` (defaults: `neo4j` / `changeme`).
- **Groq/LLM:** `python backend/scripts/llm_smoke_test.py "hello"` should print a real model
  response.
- **Backend API:** with `uvicorn` running (and `ingestion.embed_store` already run at least
  once), `curl http://localhost:8000/query -X POST -d '{"question":"why did pump P-101 fail"}'`
  (swap the port if you changed `API_PORT`) should return a grounded answer citing the P-101
  incident reports, with non-empty `citations` and a `confidence` around 0.7-0.8.
- **Frontend:** `pnpm run dev` in `frontend/` serves the app on the first free port starting at
  [http://localhost:5173](http://localhost:5173) (Vite bumps the port if 5173+ are already in
  use — check the terminal output for the actual URL). Asking a question in the chat should
  return a real, cited answer with citation cards below it, not the old
  `(mock response — backend not wired yet)` placeholder.

### Troubleshooting

| Problem | Fix |
|---|---|
| `docker compose up -d` hangs or errors | Make sure Docker Desktop is actually running (`docker info` should not error), not just installed. |
| Port `7474`/`7687` already in use | Another Neo4j instance is running — stop it, or change the port mapping in `docker-compose.yml`. |
| Neo4j container never becomes healthy | `docker logs industrial-ki-neo4j` to see why; a first boot can take ~30-60s. |
| `GROQ_API_KEY` missing errors | Either add a key to `.env`, or set up Ollama locally and leave `GROQ_API_KEY` blank. |
| `pip install -r requirements.txt` fails with a `SyntaxError` in `olefile2.py` (or a `sys.stdout.encoding` `TypeError` right after) | You're on the Xcode Command Line Tools' Python 3.9, not a real Python 3.10+. Rebuild the venv with an explicit modern interpreter (see Prerequisites). |
| `pip install -r requirements.txt` fails on some other package | Some ingestion libs (e.g. `unstructured`) pull in native deps; check the error for a missing system library and install it (e.g. `brew install libmagic` on macOS). |
| `Address already in use` on port 8000 when starting `uvicorn` | Something else on your machine is already bound to 8000 — often another local project, or one of its Docker containers, left running. `lsof -i :8000 -sTCP:LISTEN` shows what. Rather than kill an unrelated process, just change `API_PORT`/`VITE_API_BASE_URL` in your own `.env` to a free port (e.g. 8001) — `.env` is gitignored, so this is a per-machine setting and won't affect other developers, who may well have 8000 free. |
| Frontend shows a red "Couldn't reach the knowledge base" bubble | The backend isn't running, is on the wrong port, or CORS is rejecting the origin — confirm `VITE_API_BASE_URL` in `.env` matches the port `uvicorn` printed. Also check the next row — a Groq quota error surfaces as a 500 here too. |
| `/query` returns `{"detail": "The knowledge base is temporarily unavailable..."}` (503) | Groq's free tier caps at 100,000 tokens **per day**, shared across every LLM call the whole app makes (chat, entity extraction, etc.) — it's easy to exhaust during heavy testing. It's a rolling window, not a fixed daily reset, so it recovers gradually; check the backend terminal for the actual Groq error and a "try again in Nm" estimate (also logged there: `query failed for question='...'`, via `logger.exception` — #20). To avoid waiting, either use a fresh `GROQ_API_KEY`, or blank it out in `.env` to fall back to a local Ollama model (`OLLAMA_MODEL` in `.env`, needs `ollama pull` first). |
| I changed `GROQ_API_KEY` (or anything else) in `.env` but nothing changed | `uvicorn --reload` only watches `.py` files, not `.env` — restart the backend process manually after any `.env` edit. |
| `/query` answers are always "nothing relevant was found" | `ingestion.embed_store` hasn't been run yet (or `CHROMA_PATH` points somewhere empty) — run `python -m ingestion.embed_store` from `backend/` with the venv active. |
| `embed_store.py` skips a doc with `tesseract is not installed` | Install the Tesseract binary (see Prerequisites) and make sure it's on `PATH`, then re-run ingestion — that one doc is skipped, not fatal, on the first pass. |

### Current build status

This repo is being built incrementally, issue by issue (see [Issues](../../issues)). Not
everything below is the final feature — check an issue's status before assuming a step is done:
- ✅ Repo scaffold, `.env.example`, Docker Compose for Neo4j (#1, #2)
- ✅ LLM client (Groq + Ollama fallback) + smoke test (#6)
- ✅ Frontend scaffold: React + TS + Vite + Tailwind (#21)
- ✅ Chat UI (#22)
- ✅ Public seed documents in `data/raw/` (#3) — 8 docs / 5 types, see `manifest.csv`
- ✅ Synthetic "Plant Alpha" dataset in `data/synthetic/` (#4) — 17 docs, P-101 recurrence story
- ✅ PDF/text parser (#7) — `backend/ingestion/parse_docs.py`
- ✅ OCR pipeline (#8) — `backend/ingestion/ocr.py`, 99.3% legibility on the scanned sample
- ✅ Chunking (#9) — `backend/ingestion/chunker.py`, section-boundary chunking with a
  ~500-token sliding-window fallback; tables always kept as one whole chunk
- ✅ Embedding + Chroma ingestion (#10) — `backend/ingestion/embed_store.py`
  (`bge-small-en-v1.5`), 24 docs / 192 chunks indexed from `data/raw` + `data/synthetic`
- ✅ Vector retrieval (#15) — `backend/rag/retriever.py`
- ✅ Answer generation with citations (#17) — `backend/rag/generate.py`; answers cite `[n]`
  inline, mapped back to `{doc_name, page, snippet, score}`
- ✅ Citation card component (#23) — `frontend/src/components/CitationCard.tsx`, expandable,
  with a confidence-colored badge
- ✅ `/query` wired end-to-end (#24) — `backend/main.py` now calls retrieve → generate for
  real, not a mock; frontend renders citation cards and confidence; loading/error states handled
- ✅ `/query` API endpoint (#19) — closed once #16 landed: the endpoint now runs the full
  retrieve → expand_query → generate → confidence chain with clean 4xx/5xx error handling (#20)
- ✅ Confidence scoring (#18) — `backend/rag/confidence.py`, avg top-3 similarity; verified
  visibly lower for an out-of-corpus question (0.50) than an in-corpus one (0.77)
- ✅ KG schema + Neo4j constraints (#5) — `docs/kg-schema.md` defines the node/relationship
  shape; `scripts/kg_constraints.cypher` applied to the running Neo4j container (7 uniqueness
  constraints, verified idempotent)
- ✅ API error handling + tests (#20) — `/query` validates input (empty/missing/too-long
  question -> clean 422 JSON) and catches retrieval/LLM failures (-> clean 503 JSON, logged
  server-side via `logger.exception`, no internals leaked to the client). 5 pytest cases in
  `backend/tests/test_main.py` (mocked, no real LLM calls) cover all of this; verified live too.
- 🟡 In progress: **Mobile responsive pass (#25)** — touch targets, overflow guards, and iOS
  input auto-zoom fix are in; hit and is fixing a real regression along the way (`break-words`
  was causing single short words to render letter-by-letter in the chat bubbles on desktop, a
  CSS min-content sizing quirk in the flex chain — fixed by dropping `break-words` in favor of
  `inline-block` shrink-to-fit sizing). Not yet visually confirmed — no screenshot/browser tool
  available in this environment, pending manual check.
- ✅ Entity extraction (#12) — `backend/ingestion/entity_extract.py` pulls
  `{equipment_tags, parameters, personnel, dates, regulation_refs}` per chunk via the LLM,
  cached on disk by chunk_id (`backend/entity_cache.json`, gitignored) so re-runs don't
  re-spend Groq tokens. Verified 100% equipment-tag recall on 10 real sample chunks (>80%
  threshold), and confirmed personnel/dates extract correctly where the text actually
  mentions them, not just equipment tags.
  (Note: an earlier version of this note described entity_extract.py *and* graph_writer.py as
  both done, hit by a Groq quota error mid-run — that work was never actually committed and
  couldn't be recovered from git history; #12 above is a fresh, tested implementation.)
- 🟡 In progress, blocked on Groq's **daily** token cap: **Neo4j graph writer (#13)** —
  `backend/ingestion/graph_writer.py` writes Document/Equipment/Person/Regulation nodes and
  REFERENCES/MAINTAINS/GOVERNED_BY/REPORTED_BY/LOCATED_IN relationships per
  `docs/kg-schema.md`, all via MERGE (verified idempotent — 6 unit tests against a fake
  Neo4j driver). Also applied #5's constraints for real: an earlier status note claimed 7
  constraints were live, but `SHOW CONSTRAINTS` came back empty — applied
  `kg_constraints.cypher` and reverified. Running against the full corpus hit the same
  100K-tokens/day Groq wall that blocked an earlier (uncommitted, lost) attempt at this same
  ticket: 10/26 documents written before the cap, 2 skipped intentionally (P&ID images, #11),
  14 blocked on quota. Current graph: 4/6 equipment nodes (missing T-201, V-301), 2
  relationship types live. `python -m ingestion.graph_writer` picks up where this left off
  once the quota resets (or with `GROQ_API_KEY` blanked for the Ollama fallback) —
  entity_extract.py's cache means already-processed chunks aren't re-billed.
- ✅ KG-aware query expansion (#16) — `backend/rag/kg_expand.py`, wired into `/query`.
  Detects known equipment tags in the question via regex, pulls every chunk from
  documents the graph links to that equipment straight out of Chroma by doc_id (not just
  re-ranking the existing top-k), and boosts them to the front. Verified live: for "What
  issues has C-501 had recently?", one of the two C-501 incident chunks ranked #6 on pure
  vector similarity (outside the top-5) — expand_query pulls it in, and the generated
  answer ends up citing both, including a root-cause detail that only exists in the chunk
  vector search alone would have missed. Works today against the 4/6 equipment nodes #13
  has populated so far; the rest fill in once #13 finishes.

## Architecture & Planning Notes

The five capability areas in the challenge brief (universal ingestion, expert copilot,
maintenance/RCA, compliance intelligence, lessons-learned) are five separate products. Building
all five deeply in a hackathon timeframe isn't realistic, so the approach here is: build one
shared substrate (ingestion → knowledge graph → vector index) once, then expose it through one
deep feature — the **RAG Copilot** — and three thin agentic views on top of the same data:
compliance check, RCA lookup, and a lessons-learned similarity alert.

**Ingestion (shared substrate)**
- PDFs/text: `unstructured` / `pdfplumber` for layout-aware parsing + table extraction
- Scanned docs: Tesseract OCR
- P&ID drawings: no custom CV — a vision LLM (Ollama Qwen2-VL, or Groq/Claude vision) extracts
  equipment tags + connections as JSON from the image directly
- Entity extraction: one LLM call per chunk against a JSON schema (equipment tags, parameters,
  personnel, dates, regulation refs)

**Knowledge Graph**
- Neo4j (local via Docker, or Aura Free tier)
- Schema: `Equipment`, `Document`, `Procedure`, `Person`, `Regulation`, `Incident` nodes;
  `MAINTAINS`, `REFERENCES`, `GOVERNED_BY`, `REPORTED_BY` relationships

**RAG Copilot (flagship)**
- Embeddings: `sentence-transformers` (`bge-small-en-v1.5`), local/free
- Vector DB: Chroma (embedded, zero infra)
- Generation: Groq free tier (Llama 3.1/3.3) with an Ollama local fallback
- Differentiator vs. plain RAG: the KG is queried first for entities named in the question; its
  linked documents boost/filter vector retrieval before generation. Answers include inline
  citations and a confidence score derived from retrieval similarity.
- Frontend: responsive React/Tailwind chat UI — works on mobile for field technicians, not just desktop

**Thin slices (reuse the RAG substrate, no new pipelines)**
- Compliance check: preset prompt — "check procedure X against regulation Y"
- RCA lookup: KG-linked failure history + manual sections → LLM root-cause reasoning
- Lessons-learned alert: similarity search against past incident embeddings on ingest

**Data strategy:** real plant documents aren't available, so the corpus combines public sources
(OSHA incident reports, PESO/OISD/Factory Act text, public P&ID symbol sheets) with an
LLM-synthesized fictional plant ("Plant Alpha") — one coherent equipment/incident story
(e.g. Pump P-101) that ties every feature together for the demo.

**Team split**

| Person | Owns |
|---|---|
| A | Ingestion + parsing + embeddings + vector DB, dataset curation |
| B | Knowledge graph schema, entity extraction, KG-RAG fusion logic |
| C | RAG backend (retrieval + citations + confidence) + thin-slice endpoints |
| D | Frontend: chat UI, citation cards, graph viz, mobile responsiveness |

**Rough timeline (72h)**
- 0-6h: repo, dataset synthesis, Chroma+Neo4j running
- 6-24h: ingestion + KG populated, embeddings indexed, retrieval working
- 24-40h: RAG backend with citations, frontend chat wired up
- 40-56h: KG-aware retrieval, thin-slice endpoints, graph viz
- 56-68h: mobile pass, seed the "one plant" demo story end to end, bug fixes
- 68-72h: polish + rehearse
