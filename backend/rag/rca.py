"""Root-Cause Analysis lookup (#29): fuse the knowledge graph's failure history
for a piece of equipment with the RAG substrate, and have the LLM reason about
likely root causes — with citations back to real source documents.

Reuses the existing retrieval + generation pipeline; no new ingestion.
"""
from __future__ import annotations

from common.llm_client import complete
from common.observability import observe
from rag.generate import _build_context
from rag.hybrid import hybrid_retrieve
from rag.kg_expand import expand_query, find_equipment_tags
from rag.rerank import rerank

RCA_SYSTEM_PROMPT = (
    "You are a reliability engineer performing Root Cause Analysis for an industrial "
    "plant. Using ONLY the numbered context (incident reports, work orders, inspection "
    "records, and manuals), identify the most likely root cause(s) of this equipment's "
    "recurring or recent failures. Be specific and evidence-based. Cite every claim "
    "inline with the matching [n] marker. If the evidence is thin, say so — do not "
    "speculate beyond the documents."
)


def _kg_history(tag: str) -> list[dict]:
    """Incident/work-order documents the graph links to this equipment, newest first.
    Returns [] if Neo4j is unavailable."""
    try:
        from ingestion.graph_writer import get_driver

        driver = get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (d:Document)-[:REFERENCES]->(e:Equipment {tag: $tag})
                WHERE d.doc_type IN ['incident', 'work_order', 'inspection']
                RETURN d.doc_id AS doc_id, d.title AS title, d.doc_type AS doc_type,
                       d.date AS date
                ORDER BY coalesce(d.date, '') DESC
                """,
                tag=tag,
            )
            return [dict(r) for r in result]
    except Exception:
        return []


@observe(name="rca.analyze")
def analyze_rca(equipment_tag: str, top_k: int = 6) -> dict:
    """Returns {equipment_tag, root_cause_summary, history, citations, confidence}."""
    canonical = (find_equipment_tags(equipment_tag) or [equipment_tag])[0]
    question = (
        f"What are the likely root causes of failures and recurring issues with "
        f"equipment {canonical}? Summarize the failure history and probable causes."
    )

    chunks = hybrid_retrieve(question, top_k=30, candidates=30)
    chunks = expand_query(canonical, chunks, top_k=30)
    chunks = rerank(question, chunks, top_k=top_k)

    history = _kg_history(canonical)

    if not chunks:
        return {
            "equipment_tag": canonical,
            "root_cause_summary": f"No failure history found for {canonical} in the knowledge base.",
            "history": history,
            "citations": [],
            "confidence": 0.0,
        }

    context = _build_context(chunks)
    summary = complete(f"Context:\n{context}\n\nEquipment: {canonical}", system=RCA_SYSTEM_PROMPT)

    citations = [
        {
            "doc_name": c.get("title", c.get("doc_id", "")),
            "page": c.get("page", 1),
            "snippet": c.get("text", "")[:280],
            "chunk_id": c.get("chunk_id", ""),
            "score": c.get("score", 0.0),
        }
        for c in chunks
    ]
    confidence = sum(c.get("score", 0.0) for c in chunks[:3]) / min(len(chunks), 3)

    return {
        "equipment_tag": canonical,
        "root_cause_summary": summary,
        "history": history,
        "citations": citations,
        "confidence": confidence,
    }
