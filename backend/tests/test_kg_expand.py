from rag import kg_expand


def test_find_equipment_tags_detects_known_tag():
    assert kg_expand.find_equipment_tags("What issues has C-501 had recently?") == ["C-501"]


def test_find_equipment_tags_case_insensitive_normalizes_to_canonical_case():
    assert kg_expand.find_equipment_tags("what about p-101 lately") == ["P-101"]


def test_find_equipment_tags_ignores_unknown_tokens():
    assert kg_expand.find_equipment_tags("what about Z-999 or the general area") == []


def test_find_equipment_tags_dedupes_preserving_first_occurrence_order():
    assert kg_expand.find_equipment_tags("compare V-301 and P-101, also V-301 again") == [
        "V-301",
        "P-101",
    ]


def test_expand_query_returns_base_chunks_unchanged_when_no_tag_mentioned():
    base_chunks = [{"chunk_id": "a::0", "doc_id": "a", "score": 0.9}]

    result = kg_expand.expand_query("general question with no equipment tag", base_chunks)

    assert result == base_chunks


def test_expand_query_returns_base_chunks_unchanged_when_tag_has_no_graph_links(monkeypatch):
    monkeypatch.setattr(kg_expand, "linked_doc_ids", lambda tags: set())
    base_chunks = [{"chunk_id": "a::0", "doc_id": "a", "score": 0.9}]

    result = kg_expand.expand_query("what about P-101", base_chunks)

    assert result == base_chunks


def test_expand_query_includes_kg_linked_chunk_missing_from_base(monkeypatch):
    monkeypatch.setattr(kg_expand, "linked_doc_ids", lambda tags: {"incident-1"})
    monkeypatch.setattr(
        kg_expand,
        "get_chunks_for_doc_ids",
        lambda doc_ids, embedding: [
            {"chunk_id": "incident-1::0", "doc_id": "incident-1", "score": 0.68, "text": "seen already"},
            {"chunk_id": "incident-1::1", "doc_id": "incident-1", "score": 0.57, "text": "missed by vector search"},
        ],
    )
    monkeypatch.setattr("ingestion.embed_store.embed_texts", lambda texts: [[0.1, 0.2, 0.3]])

    base_chunks = [
        {"chunk_id": "other::0", "doc_id": "other", "score": 0.9, "text": "top vector hit"},
        {"chunk_id": "incident-1::0", "doc_id": "incident-1", "score": 0.68, "text": "seen already"},
    ]

    result = kg_expand.expand_query("what happened with C-501", base_chunks, top_k=2)

    result_ids = [c["chunk_id"] for c in result]
    assert "incident-1::1" in result_ids, "the chunk vector search missed must be pulled in by the graph"
    # Both KG-linked chunks come first (boosted), regardless of the requested top_k.
    assert result_ids[:2] == ["incident-1::0", "incident-1::1"]
