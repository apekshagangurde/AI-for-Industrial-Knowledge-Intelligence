"""RRF fusion logic for hybrid retrieval (feat/production-stack).

Dense + BM25 retrieval are patched, so these run without a real embedding model
or Chroma index — they pin the fusion math and the disabled/fallback behavior.
"""
from unittest.mock import patch

import rag.hybrid as hybrid


def _chunk(cid, score):
    return {"chunk_id": cid, "text": cid, "score": score}


def test_disabled_returns_plain_dense(monkeypatch):
    monkeypatch.setattr(hybrid, "HYBRID_ENABLED", False)
    dense = [_chunk("a", 0.9), _chunk("b", 0.8), _chunk("c", 0.7)]
    with patch.object(hybrid, "dense_retrieve", return_value=dense):
        out = hybrid.hybrid_retrieve("q", top_k=2)
    assert [c["chunk_id"] for c in out] == ["a", "b"]


def test_rrf_promotes_chunk_ranked_high_in_both_lists(monkeypatch):
    monkeypatch.setattr(hybrid, "HYBRID_ENABLED", True)
    # "b" is rank-2 dense but rank-1 lexical -> RRF should lift it to the top.
    dense = [_chunk("a", 0.9), _chunk("b", 0.85), _chunk("c", 0.1)]
    lexical = [_chunk("b", 5.0), _chunk("c", 4.0), _chunk("a", 0.5)]
    with patch.object(hybrid, "dense_retrieve", return_value=dense), patch.object(
        hybrid, "_bm25_rank", return_value=lexical
    ):
        out = hybrid.hybrid_retrieve("q", top_k=3)
    assert out[0]["chunk_id"] == "b"
    assert set(c["chunk_id"] for c in out) == {"a", "b", "c"}
    assert all("rrf_score" in c for c in out)


def test_falls_back_to_dense_when_bm25_unavailable(monkeypatch):
    monkeypatch.setattr(hybrid, "HYBRID_ENABLED", True)
    dense = [_chunk("a", 0.9), _chunk("b", 0.8)]
    with patch.object(hybrid, "dense_retrieve", return_value=dense), patch.object(
        hybrid, "_bm25_rank", side_effect=ImportError("rank_bm25 missing")
    ):
        out = hybrid.hybrid_retrieve("q", top_k=1)
    assert [c["chunk_id"] for c in out] == ["a"]
