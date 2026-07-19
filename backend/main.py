"""FastAPI entrypoint (#19): exposes the RAG pipeline (#15 retrieval + #17
generation) over HTTP for the frontend chat panel (#24).
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.confidence import score_confidence
from rag.generate import generate_answer
from rag.retriever import retrieve

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

    chunks = retrieve(question, top_k=5)
    result = generate_answer(question, chunks)
    confidence = score_confidence(chunks)

    return QueryResponse(answer=result["answer"], citations=result["citations"], confidence=confidence)
