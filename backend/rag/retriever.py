"""Basic semantic search over the Chroma-indexed corpus (ingestion.embed_store)."""
from __future__ import annotations

from ingestion.embed_store import embed_texts, get_collection


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Embed `query` and return the top-k most similar chunks, each with its
    metadata and a similarity score in [0, 1] (1 = identical)."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )

    chunks = []
    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "score": max(0.0, 1 - distance),
                **metadata,
            }
        )
    return chunks
