"""Regex entity subset used by the GLiNER backend (feat/production-stack).

Equipment tags, ISO dates, and regulation refs are extracted with no model at
all — these pin that exact-match layer, which is what makes the GLiNER backend
cheap enough to dodge the Groq daily token cap.
"""
from ingestion.entity_extract import _regex_entities


def test_extracts_known_equipment_tags_case_insensitive():
    out = _regex_entities("Pump p-101 tripped; valve V-301 held. Unknown X-999 ignored.")
    assert out["equipment_tags"] == ["P-101", "V-301"]


def test_extracts_iso_dates():
    out = _regex_entities("Inspection on 2024-06-15 followed up 2024-11-25.")
    assert out["dates"] == ["2024-06-15", "2024-11-25"]


def test_extracts_regulation_refs():
    out = _regex_entities("Per 29 CFR 1910.119 and OISD-118, and the Factory Act.")
    refs = " ".join(out["regulation_refs"]).lower()
    assert "cfr" in refs
    assert "oisd" in refs


def test_empty_when_nothing_present():
    out = _regex_entities("A generic sentence with no entities.")
    assert out["equipment_tags"] == []
    assert out["dates"] == []
    assert out["regulation_refs"] == []
