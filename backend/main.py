"""FastAPI entrypoint. Issue #19: minimal /query endpoint so the frontend
chat panel (issue #24) has a real backend to call instead of its mock.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from common.llm_client import complete

app = FastAPI(title="Industrial Knowledge Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    citations: list = []
    confidence: float = 0.0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    answer = complete(request.question)
    return QueryResponse(answer=answer, citations=[], confidence=0.5)
