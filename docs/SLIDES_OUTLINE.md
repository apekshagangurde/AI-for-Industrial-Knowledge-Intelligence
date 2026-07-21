# Pitch Deck Outline (#36)

10 slides, ~4 min. Judging weights: Innovation 25 / Business Impact 25 /
Technical Excellence 20 / (demo + delivery the rest). Lead with impact, prove
with the live demo, back it with the eval numbers.

1. **Title** — "Industrial Knowledge Intelligence: Unified Asset & Operations
   Brain." Team names. One-line: "Turn 7-12 disconnected document systems into
   one queryable, cited, graph-aware copilot."

2. **The problem (Business Impact)** — the three stats from PS#8, made concrete:
   - 35% of engineers' time lost searching (McKinsey).
   - 18-22% of unplanned downtime from fragmented records (BIS).
   - The knowledge cliff: 25% of experienced engineers retire within a decade.
   Frame: "not a file-management problem — a safety, quality, and cost problem."

3. **Our approach** — one shared substrate (ingestion → knowledge graph +
   vector index), surfaced through five views. Not five products; one brain.

4. **Architecture** — the pipeline diagram: docs → parse/OCR → chunk → embed +
   entity-extract → Chroma + Neo4j → hybrid retrieve → KG-expand → rerank →
   cited answer. Name the OSS: LiteLLM, GLiNER, hybrid+RRF, FlashRank, RAGAS.

5. **Differentiator (Innovation)** — KG-RAG fusion. Show the C-501 example: a
   root-cause chunk that ranked #6 on pure vector similarity, pulled in by the
   graph and cited in the final answer. "Plain RAG would have missed it."

6. **LIVE DEMO** — the P-101 story across all 5 tabs (see DEMO_SCRIPT.md). This
   is the slide. Keep it tight; the story is the pitch.

7. **It's measured (Technical Excellence)** — the `run_eval` numbers:
   retrieval hit-rate, citation coverage, and the confidence *separation*
   between in-corpus and out-of-corpus questions. "Most teams show a demo; we
   show a benchmark."

8. **Built to scale** — the honest roadmap slide: Chroma→Qdrant/pgvector,
   Docling parsing, queue-based auto-ingestion, multi-hop KG. "MVP today, clear
   path to production." (Shows engineering maturity.)

9. **Business impact recap** — tie back: less search time, fewer downtime
   events, captured tribal knowledge. A rough "if this saves X% of Y..." number.

10. **Ask / close** — what you'd do with more time + a call to action. Repo QR +
    live URL.

## Notes
- Screens > bullet walls. Slides 6 and 7 carry the win.
- Have a recorded demo video as backup in case the live one flakes.
