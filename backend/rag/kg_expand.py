"""Query the knowledge graph for equipment named in a user's question, and pull
in every chunk from documents linked to that equipment -- the actual
differentiator vs. plain vector-only RAG (#15).

Boosting re-fetches KG-linked chunks directly from Chroma by doc_id rather than
just re-ranking the top-k vector results, so a linked document that pure vector
similarity ranked outside the top-k still makes it into the final chunk list.
"""
from __future__ import annotations

import re

from common.plant_alpha import EQUIPMENT
from ingestion.graph_writer import get_driver

KNOWN_TAGS = [e["tag"] for e in EQUIPMENT]
_TAG_PATTERN = re.compile(r"\b(" + "|".join(re.escape(t) for t in KNOWN_TAGS) + r")\b", re.IGNORECASE)
_TAG_BY_UPPER = {t.upper(): t for t in KNOWN_TAGS}


def find_equipment_tags(question: str) -> list[str]:
    """Regex-match known equipment tags literally mentioned in the question."""
    seen: list[str] = []
    for match in _TAG_PATTERN.findall(question):
        canonical = _TAG_BY_UPPER.get(match.upper())
        if canonical and canonical not in seen:
            seen.append(canonical)
    return seen


def linked_doc_ids(tags: list[str]) -> set[str]:
    """Every doc_id with a REFERENCES relationship to any of these equipment tags."""
    if not tags:
        return set()
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (d:Document)-[:REFERENCES]->(e:Equipment)
            WHERE e.tag IN $tags
            RETURN DISTINCT d.doc_id AS doc_id
            """,
            tags=tags,
        )
        return {record["doc_id"] for record in result}


def get_chunks_for_doc_ids(doc_ids: set[str], query_embedding: list[float]) -> list[dict]:
    """Fetch every chunk belonging to these doc_ids directly (a metadata filter, not a
    similarity search), scored by cosine similarity against the query so it can still
    be ranked/blended with vector-retrieved chunks."""
    from ingestion.embed_store import get_collection

    if not doc_ids:
        return []

    collection = get_collection()
    result = collection.get(
        where={"doc_id": {"$in": list(doc_ids)}},
        include=["documents", "metadatas", "embeddings"],
    )
    chunks = []
    for chunk_id, text, metadata, embedding in zip(
        result["ids"], result["documents"], result["metadatas"], result["embeddings"]
    ):
        score = float(sum(a * b for a, b in zip(query_embedding, embedding)))
        chunks.append({"chunk_id": chunk_id, "text": text, "score": max(0.0, score), **metadata})
    return chunks


def expand_query(question: str, base_chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Re-rank + extend retrieval results using the knowledge graph.

    If the question names a known equipment tag, every chunk from a document
    linked to that equipment in the graph is guaranteed to be included (boosted
    to the front), regardless of whether plain vector similarity ranked it in
    the original top-k. Falls back to `base_chunks` unchanged if no known
    equipment is mentioned, or nothing is linked to it yet in the graph.
    """
    tags = find_equipment_tags(question)
    if not tags:
        return base_chunks

    doc_ids = linked_doc_ids(tags)
    if not doc_ids:
        return base_chunks

    from ingestion.embed_store import embed_texts

    query_embedding = embed_texts([question])[0]
    kg_chunks = get_chunks_for_doc_ids(doc_ids, query_embedding)

    merged = {c["chunk_id"]: c for c in base_chunks}
    for chunk in kg_chunks:
        merged.setdefault(chunk["chunk_id"], chunk)

    kg_ids = {c["chunk_id"] for c in kg_chunks}
    boosted = [merged[cid] for cid in merged if cid in kg_ids]
    rest = sorted((merged[cid] for cid in merged if cid not in kg_ids), key=lambda c: -c["score"])
    return (boosted + rest)[: max(top_k, len(boosted))]
