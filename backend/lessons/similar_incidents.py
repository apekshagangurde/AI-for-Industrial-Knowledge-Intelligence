"""Lessons-learned similarity alert (#31): given an incident document, find the
most similar past incidents by embedding similarity, so recurring failure
patterns surface proactively instead of being rediscovered each time.

Reuses the Chroma index — no new store. Compares incident chunks against other
incident chunks and aggregates to a per-document similarity.
"""
from __future__ import annotations

from collections import defaultdict

from common.observability import observe
from ingestion.embed_store import get_collection

DEFAULT_THRESHOLD = 0.55


def _incident_embeddings(exclude_doc_id: str | None = None):
    """All incident chunks with embeddings, grouped by doc_id."""
    collection = get_collection()
    data = collection.get(
        where={"doc_type": "incident"},
        include=["embeddings", "metadatas", "documents"],
    )
    by_doc: dict[str, list] = defaultdict(list)
    for cid, emb, meta, text in zip(
        data["ids"], data["embeddings"], data["metadatas"], data["documents"]
    ):
        doc_id = (meta or {}).get("doc_id", cid.split("::")[0])
        if doc_id == exclude_doc_id:
            continue
        by_doc[doc_id].append({"chunk_id": cid, "embedding": emb, "meta": meta or {}, "text": text})
    return by_doc


def _cosine(a, b) -> float:
    # Embeddings are stored normalized (bge, normalize_embeddings=True) -> dot == cosine.
    return float(sum(x * y for x, y in zip(a, b)))


@observe(name="lessons.similar_incidents")
def find_similar_incidents(doc_id: str, top_n: int = 3, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Returns {source_doc_id, matches:[{doc_id, title, similarity, snippet}]}.

    Similarity between two incidents = best chunk-pair cosine across them (a
    single strongly-matching passage is enough to flag a recurrence).
    """
    collection = get_collection()
    source = collection.get(where={"doc_id": doc_id}, include=["embeddings", "documents", "metadatas"])
    if not source["ids"]:
        return {"source_doc_id": doc_id, "matches": [], "error": f"'{doc_id}' not found"}

    source_embs = source["embeddings"]
    others = _incident_embeddings(exclude_doc_id=doc_id)

    scored = []
    for other_doc, chunks in others.items():
        best = 0.0
        best_text = ""
        for oc in chunks:
            for se in source_embs:
                sim = _cosine(se, oc["embedding"])
                if sim > best:
                    best, best_text = sim, oc["text"]
        if best >= threshold:
            title = chunks[0]["meta"].get("title", other_doc)
            scored.append(
                {
                    "doc_id": other_doc,
                    "title": title,
                    "similarity": round(best, 3),
                    "snippet": best_text[:280],
                }
            )

    scored.sort(key=lambda m: -m["similarity"])
    return {"source_doc_id": doc_id, "matches": scored[:top_n]}
