"""Tests for #20: malformed requests get a clean 4xx JSON (no stack trace),
and an LLM/retrieval failure gets a clean 5xx JSON instead of crashing.

retrieve/generate_answer are mocked throughout so these run instantly and
never call a real LLM or embedding model.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_empty_question_returns_clean_422():
    response = client.post("/query", json={"question": "   "})
    assert response.status_code == 422
    assert "question must not be empty" in response.json()["detail"]


def test_missing_question_field_returns_clean_422():
    response = client.post("/query", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_oversized_question_returns_clean_422():
    response = client.post("/query", json={"question": "x" * 2001})
    assert response.status_code == 422
    assert "too long" in response.json()["detail"]


def test_successful_query_returns_expected_shape():
    fake_chunks = [{"score": 0.8, "doc_id": "doc1", "chunk_id": "doc1::0", "text": "x"}]
    fake_result = {"answer": "the pump failed", "citations": []}
    # Patch the retrieval entrypoint; expand_query/rerank pass the fake chunks
    # through unchanged (no known equipment tag, rerank disabled in test env).
    with patch("main.hybrid_retrieve", return_value=fake_chunks), patch(
        "main.expand_query", side_effect=lambda q, c, top_k=5: c
    ), patch("main.rerank", side_effect=lambda q, c, top_k=5: c), patch(
        "main.generate_answer", return_value=fake_result
    ):
        response = client.post("/query", json={"question": "why did it fail"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "the pump failed"
    assert body["citations"] == []
    assert 0 <= body["confidence"] <= 1


def test_llm_failure_returns_clean_503_not_a_crash():
    with patch("main.hybrid_retrieve", side_effect=RuntimeError("simulated Groq rate limit")):
        response = client.post("/query", json={"question": "why did it fail"})
    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert "simulated Groq rate limit" not in body["detail"]  # no internals leaked to the client
