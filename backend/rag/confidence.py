"""Score how much to trust an answer, from retrieval similarity alone.

Kept separate from retriever.py/generate.py so the scoring rule can change
(e.g. weight in doc_type, factor in citation coverage) without touching
retrieval or generation.
"""
from __future__ import annotations


def score_confidence(chunks: list[dict], top_n: int = 3) -> float:
    """Average cosine similarity of the top-n retrieved chunks, in [0, 1].

    0.0 when nothing was retrieved at all. Naturally lower for an
    out-of-corpus question, since Chroma still returns its nearest
    neighbors even when none of them are actually relevant — an
    off-topic query just gets low-similarity chunks back.
    """
    if not chunks:
        return 0.0
    top_scores = [c["score"] for c in chunks[:top_n]]
    return sum(top_scores) / len(top_scores)
