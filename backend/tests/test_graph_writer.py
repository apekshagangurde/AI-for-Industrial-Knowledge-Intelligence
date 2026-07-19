"""Unit tests for graph_writer's orchestration logic, using a fake Neo4j driver so
these don't depend on a live database. The Cypher itself was verified against a real
Neo4j instance (see README build-status notes for #13)."""
from ingestion import graph_writer


class FakeTx:
    def __init__(self, calls):
        self.calls = calls

    def run(self, query, **params):
        self.calls.append((" ".join(query.split()), params))


class FakeSession:
    def __init__(self, calls):
        self.calls = calls

    def execute_write(self, fn, *args, **kwargs):
        return fn(FakeTx(self.calls), *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class FakeDriver:
    def __init__(self, calls):
        self.calls = calls

    def session(self):
        return FakeSession(self.calls)


def _run(monkeypatch, doc_id, doc_type, chunk_entities, date=None):
    calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(graph_writer, "get_driver", lambda: FakeDriver(calls))
    counts = graph_writer.write_document_entities(
        doc_id, doc_type, f"Title for {doc_id}", f"data/{doc_id}.md", date, chunk_entities
    )
    return counts, calls


def test_work_order_links_person_maintains_equipment(monkeypatch):
    chunk_entities = [{"equipment_tags": ["P-101"], "personnel": ["Jane Doe"], "regulation_refs": []}]

    counts, calls = _run(monkeypatch, "wo-1", "work_order", chunk_entities)

    # relationships: Person-MAINTAINS->Equipment, Document-REFERENCES->Equipment,
    # Document-REFERENCES->Person
    assert counts == {"equipment": 1, "persons": 1, "regulations": 0, "relationships": 3}
    assert any("MERGE (p)-[:MAINTAINS]->(e)" in q for q, _ in calls)


def test_maintains_not_created_for_non_work_order_docs(monkeypatch):
    chunk_entities = [{"equipment_tags": ["P-101"], "personnel": ["Jane Doe"], "regulation_refs": []}]

    _counts, calls = _run(monkeypatch, "insp-1", "inspection_report", chunk_entities)

    assert not any("MAINTAINS" in q for q, _ in calls)


def test_incident_links_reported_by(monkeypatch):
    chunk_entities = [{"equipment_tags": ["P-101"], "personnel": ["Priya Sharma"], "regulation_refs": []}]

    counts, calls = _run(monkeypatch, "inc-1", "incident", chunk_entities, date="2024-06-15")

    assert counts["persons"] == 1
    assert any("MERGE (i)-[:REPORTED_BY]->(p)" in q for q, _ in calls)
    assert any(q == "MATCH (d:Document {doc_id: $doc_id}) SET d:Incident, d.incident_id = $doc_id, d.title = $title, d.date = $date" for q, _ in calls)


def test_same_chunk_equipment_and_regulation_creates_governed_by(monkeypatch):
    chunk_entities = [{"equipment_tags": ["P-101"], "personnel": [], "regulation_refs": ["OSHA-3132"]}]

    counts, calls = _run(monkeypatch, "reg-mention-1", "work_order", chunk_entities)

    assert counts["regulations"] == 1
    assert any("MERGE (e)-[:GOVERNED_BY]->(r)" in q for q, _ in calls)


def test_regulation_document_governs_every_equipment_it_mentions(monkeypatch):
    chunk_entities = [{"equipment_tags": ["P-101", "V-301"], "personnel": [], "regulation_refs": []}]

    counts, calls = _run(monkeypatch, "osha-3132", "regulation", chunk_entities)

    governed_by_calls = [p for q, p in calls if "MERGE (e)-[:GOVERNED_BY]->(r)" in q]
    governed_tags = {p["tag"] for p in governed_by_calls}
    assert governed_tags == {"P-101", "V-301"}
    assert all(p["code"] == "osha-3132" for p in governed_by_calls)


def test_idempotent_second_run_produces_identical_counts(monkeypatch):
    chunk_entities = [{"equipment_tags": ["P-101"], "personnel": ["Jane Doe"], "regulation_refs": ["OSHA-3132"]}]

    first_counts, _ = _run(monkeypatch, "wo-2", "work_order", chunk_entities)
    second_counts, _ = _run(monkeypatch, "wo-2", "work_order", chunk_entities)

    assert first_counts == second_counts
