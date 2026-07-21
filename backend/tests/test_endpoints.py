"""Thin-slice endpoints (#27 compliance, #29 RCA, #31 lessons, #26 graph).

The underlying functions are patched, so these pin the HTTP contract and the
clean-503-on-failure behavior without touching Neo4j, Chroma, or an LLM.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_rca_returns_summary_and_citations():
    fake = {"equipment_tag": "P-101", "root_cause_summary": "seal wear", "history": [], "citations": [], "confidence": 0.7}
    with patch("rag.rca.analyze_rca", return_value=fake):
        r = client.get("/rca/P-101")
    assert r.status_code == 200
    assert r.json()["root_cause_summary"] == "seal wear"


def test_rca_failure_is_clean_503():
    with patch("rag.rca.analyze_rca", side_effect=RuntimeError("neo4j down")):
        r = client.get("/rca/P-101")
    assert r.status_code == 503
    assert "neo4j down" not in r.json()["detail"]


def test_compliance_check_returns_gaps():
    fake = {"procedure_id": "sop1", "regulation_id": "reg1", "gaps": [], "summary": "ok", "compliant": True}
    with patch("rag.compliance.check_compliance", return_value=fake):
        r = client.post("/compliance/check", json={"procedure_id": "sop1", "regulation_id": "reg1"})
    assert r.status_code == 200
    assert r.json()["compliant"] is True


def test_compliance_missing_field_is_422():
    r = client.post("/compliance/check", json={"procedure_id": "sop1"})
    assert r.status_code == 422


def test_lessons_similar_returns_matches():
    fake = {"source_doc_id": "inc1", "matches": [{"doc_id": "inc2", "title": "t", "similarity": 0.8, "snippet": "s"}]}
    with patch("lessons.similar_incidents.find_similar_incidents", return_value=fake):
        r = client.get("/lessons/similar/inc1")
    assert r.status_code == 200
    assert r.json()["matches"][0]["doc_id"] == "inc2"


def test_graph_returns_nodes_and_links():
    fake = {"center": "P-101", "nodes": [{"id": "P-101", "name": "P-101", "type": "Equipment", "color": "#2563eb"}], "links": []}
    with patch("rag.graph_view.equipment_neighborhood", return_value=fake):
        r = client.get("/graph/P-101")
    assert r.status_code == 200
    body = r.json()
    assert body["center"] == "P-101"
    assert body["nodes"][0]["type"] == "Equipment"
