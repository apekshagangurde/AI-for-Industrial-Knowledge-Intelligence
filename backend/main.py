"""FastAPI entrypoint (#19): exposes the RAG pipeline (#15 retrieval + #17
generation) over HTTP for the frontend chat panel (#24).
"""

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from rag.confidence import score_confidence
from rag.generate import generate_answer
from rag.hybrid import hybrid_retrieve
from rag.kg_expand import expand_query
from rag.rerank import rerank

RETRIEVE_CANDIDATES = int(os.getenv("RETRIEVE_CANDIDATES", "30"))
TOP_K = 5

app = FastAPI(title="Industrial Knowledge Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class Citation(BaseModel):
    doc_name: str
    page: int
    snippet: str
    chunk_id: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    confidence: float = 0.0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be empty")
    if len(question) > 2000:
        raise HTTPException(
            status_code=422, detail="question is too long (max 2000 characters)"
        )

    try:
        # 1. Hybrid retrieval (dense + BM25, RRF-fused) pulls a wide candidate pool.
        chunks = hybrid_retrieve(question, top_k=RETRIEVE_CANDIDATES, candidates=RETRIEVE_CANDIDATES)
        # 2. KG expansion guarantees docs the graph links to named equipment are present.
        chunks = expand_query(question, chunks, top_k=RETRIEVE_CANDIDATES)
        # 3. Cross-encoder rerank for precision, trimmed to the final top_k.
        chunks = rerank(question, chunks, top_k=TOP_K)
        result = generate_answer(question, chunks)
    except Exception:
        logger.exception("query failed for question=%r", question)
        raise HTTPException(
            status_code=503,
            detail="The knowledge base is temporarily unavailable (retrieval or LLM error). Please try again shortly.",
        )

    confidence = score_confidence(chunks)

    return QueryResponse(
        answer=result["answer"], citations=result["citations"], confidence=confidence
    )


# --- Thin agentic slices over the same RAG/KG substrate --------------------

class ComplianceRequest(BaseModel):
    procedure_id: str
    regulation_id: str


def _unavailable(what: str):
    raise HTTPException(
        status_code=503,
        detail=f"{what} is temporarily unavailable (retrieval, graph, or LLM error). Please try again shortly.",
    )


@app.get("/rca/{equipment_tag}")
def rca(equipment_tag: str):
    """#29 — Root-Cause Analysis: KG failure history + LLM reasoning, cited."""
    from rag.rca import analyze_rca

    try:
        return analyze_rca(equipment_tag)
    except Exception:
        logger.exception("rca failed for equipment_tag=%r", equipment_tag)
        _unavailable("RCA")


@app.post("/compliance/check")
def compliance_check(request: ComplianceRequest):
    """#27 — Compliance gap check between a procedure and a regulation."""
    from rag.compliance import check_compliance

    try:
        return check_compliance(request.procedure_id, request.regulation_id)
    except Exception:
        logger.exception(
            "compliance check failed for procedure=%r regulation=%r",
            request.procedure_id, request.regulation_id,
        )
        _unavailable("Compliance check")


@app.get("/lessons/similar/{doc_id}")
def lessons_similar(doc_id: str):
    """#31 — Lessons-learned: surface past incidents similar to this one."""
    from lessons.similar_incidents import find_similar_incidents

    try:
        return find_similar_incidents(doc_id)
    except Exception:
        logger.exception("lessons lookup failed for doc_id=%r", doc_id)
        _unavailable("Lessons-learned lookup")


@app.get("/graph/{equipment_tag}")
def graph(equipment_tag: str):
    """#26 — Knowledge-graph neighborhood for the visualization tab."""
    from rag.graph_view import equipment_neighborhood

    try:
        return equipment_neighborhood(equipment_tag)
    except Exception:
        logger.exception("graph lookup failed for equipment_tag=%r", equipment_tag)
        _unavailable("Graph view")
