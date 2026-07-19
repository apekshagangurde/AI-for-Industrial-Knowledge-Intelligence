import json

from ingestion import entity_extract


def test_parse_and_validate_accepts_well_formed_json():
    response = json.dumps(
        {
            "equipment_tags": ["P-101"],
            "parameters": ["pressure"],
            "personnel": ["Jane Doe"],
            "dates": ["2024-06-15"],
            "regulation_refs": ["29 CFR 1910.119"],
        }
    )

    result = entity_extract._parse_and_validate(response)

    assert result == {
        "equipment_tags": ["P-101"],
        "parameters": ["pressure"],
        "personnel": ["Jane Doe"],
        "dates": ["2024-06-15"],
        "regulation_refs": ["29 CFR 1910.119"],
    }


def test_parse_and_validate_filters_hallucinated_equipment_tags():
    response = json.dumps({"equipment_tags": ["P-101", "Z-999"]})

    result = entity_extract._parse_and_validate(response)

    assert result["equipment_tags"] == ["P-101"]


def test_parse_and_validate_returns_empty_on_garbage_response():
    result = entity_extract._parse_and_validate("not json at all, sorry")

    assert result == entity_extract.EMPTY_ENTITIES


def test_extract_entities_for_chunks_only_calls_llm_for_uncached_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(entity_extract, "CACHE_PATH", tmp_path / "entity_cache.json")

    call_count = {"n": 0}

    def fake_complete(prompt, system=None):
        call_count["n"] += 1
        return json.dumps({"equipment_tags": ["P-101"]})

    monkeypatch.setattr(entity_extract, "complete", fake_complete)

    chunks = [
        {"chunk_id": "doc::0", "text": "P-101 was inspected."},
        {"chunk_id": "doc::1", "text": "V-301 was tested."},
    ]

    first = entity_extract.extract_entities_for_chunks(chunks)
    assert call_count["n"] == 2
    assert first["doc::0"]["equipment_tags"] == ["P-101"]

    # Re-running with the same chunk_ids must hit the cache, not the LLM again.
    second = entity_extract.extract_entities_for_chunks(chunks)
    assert call_count["n"] == 2
    assert second == first
