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
- Python 3.10+
- Node.js 18+ and npm
- A free [Groq API key](https://console.groq.com) (console.groq.com → API Keys → Create API Key)
  — takes about a minute, no credit card. Local [Ollama](https://ollama.com) works as an offline
  fallback if you'd rather not sign up for anything.

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/apekshagangurde/AI-for-Industrial-Knowledge-Intelligence.git
cd AI-for-Industrial-Knowledge-Intelligence

# 2. Configure environment
cp .env.example .env
# open .env and paste your GROQ_API_KEY (or set up Ollama — see .env.example comments)

# 3. Start local infra (Neo4j knowledge graph)
docker compose up -d

# 4. Backend — Python virtual env + dependencies
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ..

# 5. Frontend — once issue #21 has scaffolded frontend/ with Vite
cd frontend
npm install
npm run dev
```

### Verify your setup

- **Neo4j:** `docker ps --filter name=industrial-ki-neo4j` should show `Up ... (healthy)`.
  Open [http://localhost:7474](http://localhost:7474) and log in with the `NEO4J_USER` /
  `NEO4J_PASSWORD` from your `.env` (defaults: `neo4j` / `changeme`).
- **Groq/LLM:** once issue #6 lands, run `python backend/scripts/llm_smoke_test.py "hello"` —
  it should print a real model response.
- **Backend API:** once issue #19 lands, `curl http://localhost:8000/query -X POST -d '{"question":"..."}'`
  should return JSON with `answer`, `citations`, and `confidence`.
- **Frontend:** once issue #21 lands, `npm run dev` in `frontend/` should serve the app at
  [http://localhost:5173](http://localhost:5173).

### Troubleshooting

| Problem | Fix |
|---|---|
| `docker compose up -d` hangs or errors | Make sure Docker Desktop is actually running (`docker info` should not error), not just installed. |
| Port `7474`/`7687` already in use | Another Neo4j instance is running — stop it, or change the port mapping in `docker-compose.yml`. |
| Neo4j container never becomes healthy | `docker logs industrial-ki-neo4j` to see why; a first boot can take ~30-60s. |
| `GROQ_API_KEY` missing errors | Either add a key to `.env`, or set up Ollama locally and leave `GROQ_API_KEY` blank. |
| `pip install -r requirements.txt` fails on a package | Some ingestion libs (e.g. `unstructured`) pull in native deps; check the error for a missing system library and install it (e.g. `brew install libmagic` on macOS). |

### Current build status

This repo is being built incrementally, issue by issue (see [Issues](../../issues)). Not
everything above works yet — check an issue's status before assuming a step is live:
- ✅ Repo scaffold, `.env.example`, Docker Compose for Neo4j (#1, #2)
- ✅ LLM client (Groq + Ollama fallback) + smoke test (#6)
- ✅ Frontend scaffold: React + TS + Vite + Tailwind (#21)
- ✅ Chat UI (#22) — mock responses until #24 wires up the real API
- ✅ Public seed documents in `data/raw/` (#3) — 8 docs / 5 types, see `manifest.csv`
- ✅ Synthetic "Plant Alpha" dataset in `data/synthetic/` (#4) — 17 docs, P-101 recurrence story
- ✅ PDF/text parser (#7) — `backend/ingestion/parse_docs.py`
- ⏳ OCR (#8), chunking (#9), RAG backend — in progress

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
