"""Hybrid retrieval: dense vectors + BM25 lexical, fused with Reciprocal Rank
Fusion (RRF).

Dense embeddings (bge-small) are weak at exact-token match — and industrial
docs are full of exact tokens: equipment tags (P-101), part numbers, regulation
codes (29 CFR 1910.119). BM25 nails those; dense nails paraphrase/semantics.
RRF combines the two ranked lists without needing to calibrate their score
scales:  rrf(d) = sum over lists of 1 / (k + rank_i(d)),  k = 60 (standard).

Enabled by HYBRID_SEARCH=1. If rank_bm25 isn't installed, `hybrid_retrieve`
transparently falls back to plain dense retrieval.
"""
from __future__ import annotations

import os
import re

from ingestion.embed_store import embed_texts, get_collection
from rag.retriever import retrieve as dense_retrieve

HYBRID_ENABLED = os.getenv("HYBRID_SEARCH", "").strip().lower() in ("1", "true", "yes")
RRF_K = 60

_bm25 = None
_bm25_ids: list[str] = []
_bm25_docs: list[dict] = []


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-\./]*", text.lower())


def _build_bm25():
    """Build a BM25 index over the whole Chroma corpus (cached process-wide).

    Fine for the demo corpus (~200 chunks). At real scale this belongs in the
    vector store itself (Qdrant/Weaviate native hybrid, pgvector + tsvector) —
    see docs/PRODUCTION_STACK.md.
    """
    global _bm25, _bm25_ids, _bm25_docs
    from rank_bm25 import BM25Okapi

    collection = get_collection()
    data = collection.get(include=["documents", "metadatas"])
    _bm25_ids = data["ids"]
    _bm25_docs = [
        {"chunk_id": cid, "text": text, **(meta or {})}
        for cid, text, meta in zip(data["ids"], data["documents"], data["metadatas"])
    ]
    _bm25 = BM25Okapi([_tokenize(d["text"]) for d in _bm25_docs])


def _bm25_rank(query: str, limit: int) -> list[dict]:
    if _bm25 is None:
        _build_bm25()
    if not _bm25_docs:
        return []
    scores = _bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:limit]
    return [dict(_bm25_docs[i], score=float(scores[i])) for i in ranked]


def hybrid_retrieve(query: str, top_k: int = 5, candidates: int = 30) -> list[dict]:
    """Return up to top_k chunks, fusing dense + BM25 rankings via RRF.

    Pulls `candidates` from each retriever before fusing so a chunk strong in
    only one modality still surfaces. Falls back to plain dense retrieval when
    hybrid is disabled or rank_bm25 is unavailable.
    """
    dense = dense_retrieve(query, top_k=candidates)
    if not HYBRID_ENABLED:
        return dense[:top_k]

    try:
        lexical = _bm25_rank(query, candidates)
    except Exception:
        return dense[:top_k]

    # RRF fusion over the two ranked lists, keyed by chunk_id.
    fused: dict[str, float] = {}
    by_id: dict[str, dict] = {}
    for ranked in (dense, lexical):
        for rank, chunk in enumerate(ranked):
            cid = chunk["chunk_id"]
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + rank)
            by_id.setdefault(cid, chunk)

    order = sorted(fused, key=lambda cid: -fused[cid])
    result = []
    for cid in order[:top_k]:
        chunk = dict(by_id[cid])
        chunk["rrf_score"] = fused[cid]
        result.append(chunk)
    return result


def reset_bm25_cache() -> None:
    """Drop the in-memory BM25 index (call after re-ingesting the corpus)."""
    global _bm25, _bm25_ids, _bm25_docs
    _bm25, _bm25_ids, _bm25_docs = None, [], []
