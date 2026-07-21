"""Cross-encoder reranking (FlashRank) over retrieved candidates.

Dense/hybrid retrieval is recall-oriented — it pulls a wide candidate pool.
A cross-encoder then scores each (query, chunk) pair jointly for precision,
which is where most of the answer-quality lift comes from. FlashRank runs a
quantized cross-encoder on CPU in well under 100ms for a ~30-candidate pool.

Enabled by RERANK=1. Degrades to a no-op (returns candidates unchanged,
trimmed to top_k) if flashrank isn't installed — never fatal.
"""
from __future__ import annotations

import os

RERANK_ENABLED = os.getenv("RERANK", "").strip().lower() in ("1", "true", "yes")
RERANK_MODEL = os.getenv("RERANK_MODEL", "ms-marco-MiniLM-L-12-v2")

_ranker = None


def _get_ranker():
    global _ranker
    if _ranker is None:
        from flashrank import Ranker  # raises ImportError -> caller no-ops

        _ranker = Ranker(model_name=RERANK_MODEL)
    return _ranker


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Reorder `chunks` by cross-encoder relevance to `query`, keep top_k.

    Writes the reranker score back onto each chunk as `rerank_score` and
    replaces `score` with it (so downstream confidence uses the better signal).
    No-op passthrough (trimmed to top_k) when disabled or unavailable.
    """
    if not RERANK_ENABLED or not chunks:
        return chunks[:top_k]

    try:
        from flashrank import RerankRequest

        ranker = _get_ranker()
    except Exception:
        return chunks[:top_k]

    passages = [
        {"id": i, "text": c.get("text", ""), "meta": {}} for i, c in enumerate(chunks)
    ]
    try:
        results = ranker.rerank(RerankRequest(query=query, passages=passages))
    except Exception:
        return chunks[:top_k]

    reranked = []
    for r in results:
        chunk = dict(chunks[r["id"]])
        chunk["rerank_score"] = float(r["score"])
        chunk["score"] = float(r["score"])
        reranked.append(chunk)
    return reranked[:top_k]
