"""Reranker wrapper behavior (feat/production-stack).

FlashRank itself is patched — these pin the enable/disable/fallback contract,
not the model's relevance quality.
"""
from unittest.mock import patch

import rag.rerank as rerank_mod


def _chunks():
    return [
        {"chunk_id": "a", "text": "irrelevant", "score": 0.9},
        {"chunk_id": "b", "text": "the answer", "score": 0.4},
        {"chunk_id": "c", "text": "noise", "score": 0.3},
    ]


def test_disabled_is_passthrough_trimmed(monkeypatch):
    monkeypatch.setattr(rerank_mod, "RERANK_ENABLED", False)
    out = rerank_mod.rerank("q", _chunks(), top_k=2)
    assert [c["chunk_id"] for c in out] == ["a", "b"]


def test_reranks_and_rewrites_score(monkeypatch):
    monkeypatch.setattr(rerank_mod, "RERANK_ENABLED", True)

    class FakeRanker:
        def rerank(self, req):
            # Reverse-relevance: promote "b" (index 1) to the front.
            return [
                {"id": 1, "score": 0.99},
                {"id": 0, "score": 0.20},
                {"id": 2, "score": 0.10},
            ]

    with patch.object(rerank_mod, "_get_ranker", return_value=FakeRanker()), patch.dict(
        "sys.modules", {"flashrank": __import__("types").SimpleNamespace(RerankRequest=lambda **k: k)}
    ):
        out = rerank_mod.rerank("q", _chunks(), top_k=2)
    assert [c["chunk_id"] for c in out] == ["b", "a"]
    assert out[0]["score"] == 0.99
    assert out[0]["rerank_score"] == 0.99


def test_falls_back_to_passthrough_on_error(monkeypatch):
    monkeypatch.setattr(rerank_mod, "RERANK_ENABLED", True)
    with patch.object(rerank_mod, "_get_ranker", side_effect=ImportError("flashrank missing")):
        out = rerank_mod.rerank("q", _chunks(), top_k=2)
    assert [c["chunk_id"] for c in out] == ["a", "b"]
