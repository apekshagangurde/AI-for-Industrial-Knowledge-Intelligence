"""Run the RAG pipeline over a benchmark set and report quality metrics.

Two layers, so this is useful with or without extra deps/keys:

1. Always-on, zero-dependency metrics computed from the pipeline output itself:
   - retrieval hit-rate: did the citations include an expected equipment tag /
     document for the question?
   - citation coverage: fraction of answered questions that cited >=1 source.
   - confidence separation: mean confidence on in-corpus vs out-of-corpus
     questions (a healthy system scores the out-of-corpus question much lower).

2. RAGAS metrics (faithfulness, answer relevancy, context precision) when the
   `ragas` package is installed AND an LLM judge is reachable. Skipped cleanly
   otherwise, with a note — never fatal.

Usage (from backend/, venv active, after `python -m ingestion.embed_store`):
    python -m evaluation.run_eval
    python -m evaluation.run_eval --ragas       # also run RAGAS if available
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rag.confidence import score_confidence
from rag.generate import generate_answer
from rag.hybrid import hybrid_retrieve
from rag.kg_expand import expand_query
from rag.rerank import rerank

HERE = Path(__file__).resolve().parent
BENCHMARK = HERE / "benchmark.jsonl"
RESULTS = HERE / "results.json"

RETRIEVE_CANDIDATES = int(os.getenv("RETRIEVE_CANDIDATES", "30"))
TOP_K = 5


def _load_benchmark() -> list[dict]:
    return [json.loads(line) for line in BENCHMARK.read_text().splitlines() if line.strip()]


def _run_pipeline(question: str) -> dict:
    chunks = hybrid_retrieve(question, top_k=RETRIEVE_CANDIDATES, candidates=RETRIEVE_CANDIDATES)
    chunks = expand_query(question, chunks, top_k=RETRIEVE_CANDIDATES)
    chunks = rerank(question, chunks, top_k=TOP_K)
    result = generate_answer(question, chunks)
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "confidence": score_confidence(chunks),
        "chunks": chunks,
    }


def _retrieval_hit(case: dict, out: dict) -> bool:
    """Did retrieval surface something the question expected?"""
    cited_text = " ".join(
        f"{c.get('doc_name', '')} {c.get('chunk_id', '')} {c.get('snippet', '')}"
        for c in out["citations"]
    ).lower()
    chunk_text = " ".join(c.get("text", "") for c in out["chunks"]).lower()
    haystack = cited_text + " " + chunk_text

    for tag in case.get("expects_equipment", []):
        if tag.lower() in haystack:
            return True
    sub = case.get("expects_doc_substring", "")
    if sub and sub.lower() in haystack:
        return True
    # No specific expectation -> a non-empty citation counts as a hit.
    return not case.get("expects_equipment") and not sub and bool(out["citations"])


def run(with_ragas: bool = False) -> dict:
    cases = _load_benchmark()
    rows = []
    in_conf, out_conf = [], []

    print(f"\nRunning {len(cases)} benchmark questions through the pipeline...\n")
    for case in cases:
        out = _run_pipeline(case["question"])
        hit = _retrieval_hit(case, out) if case.get("in_corpus", True) else None
        (in_conf if case.get("in_corpus", True) else out_conf).append(out["confidence"])
        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "in_corpus": case.get("in_corpus", True),
                "confidence": round(out["confidence"], 3),
                "n_citations": len(out["citations"]),
                "retrieval_hit": hit,
                "answer": out["answer"][:200],
            }
        )
        flag = "—" if hit is None else ("HIT " if hit else "MISS")
        print(f"  [{case['id']}] {flag}  conf={out['confidence']:.2f}  cites={len(out['citations'])}  {case['question'][:54]}")

    in_corpus = [r for r in rows if r["in_corpus"]]
    hits = [r for r in in_corpus if r["retrieval_hit"]]
    answered = [r for r in in_corpus if r["n_citations"] > 0]

    summary = {
        "n_questions": len(cases),
        "retrieval_hit_rate": round(len(hits) / max(len(in_corpus), 1), 3),
        "citation_coverage": round(len(answered) / max(len(in_corpus), 1), 3),
        "mean_confidence_in_corpus": round(sum(in_conf) / max(len(in_conf), 1), 3),
        "mean_confidence_out_corpus": round(sum(out_conf) / max(len(out_conf), 1), 3) if out_conf else None,
    }

    print("\n=== Summary ===")
    print(f"  Retrieval hit-rate (in-corpus):   {summary['retrieval_hit_rate']:.1%}")
    print(f"  Citation coverage:                {summary['citation_coverage']:.1%}")
    print(f"  Mean confidence  in-corpus:       {summary['mean_confidence_in_corpus']:.2f}")
    if summary["mean_confidence_out_corpus"] is not None:
        gap = summary["mean_confidence_in_corpus"] - summary["mean_confidence_out_corpus"]
        print(f"  Mean confidence  out-of-corpus:   {summary['mean_confidence_out_corpus']:.2f}  (separation {gap:+.2f})")

    if with_ragas:
        summary["ragas"] = _run_ragas(cases)

    RESULTS.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print(f"\nWrote per-question results -> {RESULTS}\n")
    return summary


def _run_ragas(cases: list[dict]) -> dict | str:
    """Optional deeper metrics. Returns a note string if RAGAS can't run."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, faithfulness
    except Exception as exc:
        note = f"RAGAS skipped (install `ragas datasets`): {exc}"
        print(f"\n{note}")
        return note

    records = {"question": [], "answer": [], "contexts": []}
    for case in cases:
        if not case.get("in_corpus", True):
            continue
        out = _run_pipeline(case["question"])
        records["question"].append(case["question"])
        records["answer"].append(out["answer"])
        records["contexts"].append([c.get("text", "") for c in out["chunks"]])

    try:
        ds = Dataset.from_dict(records)
        scores = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision])
        print("\n=== RAGAS ===")
        print(f"  {scores}")
        return {k: float(v) for k, v in scores.items()} if hasattr(scores, "items") else str(scores)
    except Exception as exc:
        note = f"RAGAS ran but failed (needs a reachable LLM judge / OPENAI_API_KEY): {exc}"
        print(f"\n{note}")
        return note


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ragas", action="store_true", help="also run RAGAS metrics if available")
    args = parser.parse_args()
    run(with_ragas=args.ragas)
