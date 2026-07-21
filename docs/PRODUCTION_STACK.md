# Production Stack Upgrades

This branch (`feat/production-stack`) hardens the hackathon MVP toward a real,
scalable system without breaking the working demo. Every change is **additive
and feature-flagged** — with the new env flags unset, the app behaves exactly as
before. Each library degrades gracefully (logged, never fatal) if it isn't
installed or its backing service is down.

## What changed

| Capability | Before | Now | Flag |
|---|---|---|---|
| LLM calls | direct Groq/Ollama `if/else` | **LiteLLM** gateway: fallback chain, retries, JSON + vision modes | `USE_LITELLM=1` |
| Retrieval | dense-only top-5 (`bge-small`) | **Hybrid** dense + BM25, fused with RRF (k=60) | `HYBRID_SEARCH=1` |
| Ranking | raw cosine order | **FlashRank** cross-encoder rerank of a wide candidate pool | `RERANK=1` |
| Entity extraction | 1 LLM call/chunk (Groq quota wall) | **GLiNER** encoder NER + regex; no LLM tokens | `ENTITY_BACKEND=gliner` |
| Evaluation | none | **RAGAS** + zero-dep retrieval/confidence metrics | `python -m evaluation.run_eval` |
| Observability | none | **Langfuse** tracing (no-op unless keys set) | `LANGFUSE_*` |

## Query pipeline now

```
question
  → hybrid_retrieve   (dense + BM25, RRF-fused, wide candidate pool)
  → expand_query      (KG: pull docs linked to named equipment)
  → rerank            (cross-encoder precision, trim to top-5)
  → generate_answer   (cited, grounded)
  → score_confidence
```

## Why these (2026 landscape)

- **LiteLLM** (~51k★) — the standard OSS LLM gateway; one API, provider
  fallback, per-key budgets. Directly addresses the single-provider Groq
  quota block.
- **Hybrid + RRF** — dense embeddings miss exact tokens (equipment tags like
  `P-101`, reg codes like `29 CFR 1910.119`); BM25 nails them. RRF fuses both
  ranked lists without score-scale calibration.
- **FlashRank** — sub-100ms CPU cross-encoder; biggest precision lift per line
  of code, no external API.
- **GLiNER** — encoder NER, orders of magnitude cheaper than per-chunk LLM
  extraction; unblocks graph ingestion under the Groq daily cap.
- **RAGAS** — maps directly onto the challenge's evaluation focus (answer
  quality, faithfulness). Gives a *measured* accuracy story.

## Run it

```bash
cd backend && source .venv/bin/activate
pip install -r requirements.txt          # pulls the new libs
python -m ingestion.embed_store          # (re)build the index
uvicorn main:app --reload                # flags read from .env

# measure quality
python -m evaluation.run_eval            # zero-dep metrics
python -m evaluation.run_eval --ragas    # + RAGAS if installed & judge reachable
```

## Not yet swapped (next steps — see README "Architecture & Planning Notes")

These are the higher-effort scale moves, deliberately left for a follow-up so
this branch stays low-risk:

- **Vector store**: Chroma (embedded) → **Qdrant** or **pgvector** for
  concurrency, native hybrid, metadata ACLs, and scale beyond ~10⁴ chunks.
  `rag/hybrid.py` builds BM25 in-process — fine for the demo corpus, belongs in
  the store at scale.
- **Doc parsing**: unstructured/pdfplumber → **Docling** (better tables, layout,
  scanned docs, P&ID-friendly).
- **Async ingestion**: batch script → upload endpoint + queue (Arq/Celery) so
  the graph "updates as new records arrive" (per the challenge brief).
- **KG depth**: traverse `MAINTAINS`/`GOVERNED_BY`/`REPORTED_BY`/Incident
  multi-hop (currently `REFERENCES` only); evaluate LightRAG / neo4j-graphrag.

## Verification status

Code written and unit-tested (mocked) but **not yet run end-to-end** in this
environment (no venv / Neo4j / Groq key here). Before relying on it: create the
venv, `pip install -r requirements.txt`, run `embed_store`, then `run_eval` to
confirm the metrics move in the right direction.
