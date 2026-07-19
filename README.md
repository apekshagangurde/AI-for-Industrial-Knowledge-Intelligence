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

## Getting Started

1. Copy `.env.example` to `.env` and fill in `GROQ_API_KEY` (free tier at
   [console.groq.com](https://console.groq.com)) — or leave blank to use the local Ollama fallback.
2. Bring up local infra: `docker compose up -d` (Neo4j + Chroma — see issue #2).
3. Backend: `cd backend && pip install -r requirements.txt`
4. Frontend: `cd frontend && npm install && npm run dev` (after issue #21 scaffolds it)

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
