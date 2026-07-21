# Demo Script — the P-101 story across all 5 features (#33)

One asset, one narrative, every feature. The synthetic "Plant Alpha" corpus (#4)
was built so **Feed Pump P-101** has a recurring-failure story that touches
ingestion → graph → copilot → RCA → compliance → lessons. Follow this order live.

> Before demoing: run `python -m ingestion.run_pipeline` (embeds + graph) and
> `python -m evaluation.run_eval` — the eval numbers are a slide (see below).
> Warm the backend if deployed (hit `/health`).

## 0. The hook (30s, no clicks)
"Plant engineers spend ~35% of their time hunting for information across 7-12
disconnected systems. When P-101 keeps failing, the answer is already in the
documents — just scattered. Watch us pull it together."

## 1. Copilot tab — the flagship (60s)
- Ask: **"Why does feed pump P-101 keep failing?"**
- Point out: grounded answer, inline `[n]` citations, citation cards, a
  confidence badge. This is RAG + KG fusion — the graph pulled in a linked
  incident chunk pure vector search ranked too low.
- Contrast: ask **"What is the capital of France?"** → it refuses and the
  confidence drops. Honest system, not a hallucinating chatbot.

## 2. Graph tab — "collective intelligence" (30s)
- Select **P-101** → the neighborhood renders: the pump linked to its
  incidents, work orders, inspections, regulations, people. Colored by type.
- Line: "Every edge here was extracted automatically from unstructured docs."

## 3. RCA tab — maintenance intelligence (45s)
- Select **P-101** → root-cause summary + the linked failure history + citations.
- Line: "It's connecting dots across months of records no single technician
  would hold in their head."

## 4. Compliance tab — regulatory intelligence (45s)
- Procedure `2023-02-15_centrifugal-pump-operation`, regulation
  `osha_process_safety_management` → severity-tagged gap list.
- Line: "Maps what the procedure does against what the regulation requires."

## 5. Lessons tab — proactive pattern detection (30s)
- Enter a P-101 incident doc_id → similar past incidents surface with a
  similarity score.
- Line: "Before the next failure, it flags: we've seen this pattern before."

## Close (20s)
"One ingestion substrate — knowledge graph + vector index — surfaced through
five views. Built on OSS the industry already trusts (LiteLLM, GLiNER, hybrid
retrieval, RAGAS-measured). Retires the knowledge cliff instead of widening it."

## Exact doc_ids to verify beforehand
Run `python -c "import csv;[print(r['filename']) for r in csv.DictReader(open('data/synthetic/manifest.csv'))]"`
and confirm the procedure/regulation/incident IDs above still match the corpus.
Fix any mismatch here before the live run (that's the whole point of #33).
