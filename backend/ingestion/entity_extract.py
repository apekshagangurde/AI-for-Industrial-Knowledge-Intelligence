"""Extract graph-worthy entities from a chunk's text via the LLM.

Feeds the Neo4j graph writer (#13): equipment tags, parameters, personnel,
dates, and regulation references pulled out of each chunk. Results are
cached on disk keyed by chunk_id, so re-running ingestion doesn't re-spend
LLM calls (and Groq free-tier tokens) on chunks already processed.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from common.llm_client import complete
from common.plant_alpha import EQUIPMENT

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = REPO_ROOT / "backend" / "entity_cache.json"

KNOWN_TAGS = {e["tag"] for e in EQUIPMENT}

# "gliner" (default): encoder NER, no LLM tokens spent — unblocks graph
# ingestion when the Groq daily cap is exhausted. "llm": original per-chunk
# LLM extraction. Falls back to "llm" automatically if GLiNER can't load.
ENTITY_BACKEND = os.getenv("ENTITY_BACKEND", "gliner").strip().lower()
GLINER_MODEL = os.getenv("GLINER_MODEL", "urchade/gliner_medium-v2.1")

# Structured entities that are cheap and exact via regex — no model needed for
# these regardless of backend. Equipment tags are matched against the known
# fixture list; dates and regulation refs use industrial-format patterns.
_TAG_RX = re.compile(r"\b(" + "|".join(re.escape(t) for t in KNOWN_TAGS) + r")\b", re.IGNORECASE)
_DATE_RX = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_REG_RX = re.compile(
    r"\b(?:\d+\s*CFR\s*\d+(?:\.\d+)?|OISD[- ]?\w+|IS[- ]?\d+|PESO|Factory\s+Act|"
    r"29\s*CFR\s*1910(?:\.\d+)?)\b",
    re.IGNORECASE,
)
_TAG_BY_UPPER = {t.upper(): t for t in KNOWN_TAGS}

_gliner_model = None

SYSTEM_PROMPT = (
    "You extract structured entities from industrial documents. Output strict JSON "
    "matching the requested schema and nothing else -- no commentary, no markdown fences."
)

_SCHEMA_HINT = """Return a JSON object with exactly these keys:
{
  "equipment_tags": ["P-101"],
  "parameters": ["pressure", "temperature"],
  "personnel": ["Jane Doe"],
  "dates": ["2024-06-15"],
  "regulation_refs": ["29 CFR 1910.119"]
}
Use an empty list for any category with nothing found. Only include an equipment tag if it
literally appears in the text (format like P-101, T-201, HX-401, V-301, C-501)."""

EMPTY_ENTITIES = {
    "equipment_tags": [],
    "parameters": [],
    "personnel": [],
    "dates": [],
    "regulation_refs": [],
}


def extract_entities(chunk_text: str) -> dict:
    """Returns {equipment_tags, parameters, personnel, dates, regulation_refs}.

    Dispatches to the GLiNER (encoder NER) backend by default — no LLM tokens
    spent — or the original LLM backend when ENTITY_BACKEND=llm. GLiNER
    automatically falls back to the LLM path if the model can't be loaded.
    """
    if ENTITY_BACKEND == "gliner":
        entities = _extract_entities_gliner(chunk_text)
        if entities is not None:
            return entities
    return _extract_entities_llm(chunk_text)


def _extract_entities_llm(chunk_text: str) -> dict:
    prompt = f"{_SCHEMA_HINT}\n\nText:\n{chunk_text}"
    response = complete(prompt, system=SYSTEM_PROMPT)
    return _parse_and_validate(response)


def _regex_entities(chunk_text: str) -> dict:
    """The exact-match subset (equipment tags, dates, regulation refs) that never
    needs a model."""
    tags = {_TAG_BY_UPPER[m.upper()] for m in _TAG_RX.findall(chunk_text)}
    return {
        "equipment_tags": sorted(tags),
        "parameters": [],
        "personnel": [],
        "dates": sorted(set(_DATE_RX.findall(chunk_text))),
        "regulation_refs": sorted({m.strip() for m in _REG_RX.findall(chunk_text)}),
    }


def _get_gliner():
    global _gliner_model
    if _gliner_model is None:
        from gliner import GLiNER  # raises ImportError -> caller falls back to LLM

        _gliner_model = GLiNER.from_pretrained(GLINER_MODEL)
    return _gliner_model


def _extract_entities_gliner(chunk_text: str) -> dict | None:
    """GLiNER for the fuzzy entities (personnel, process parameters) + regex for
    the exact ones. Returns None if GLiNER can't be loaded, so the caller can
    degrade to the LLM backend."""
    fields = _regex_entities(chunk_text)
    try:
        model = _get_gliner()
    except Exception:
        return None

    labels = ["person", "process parameter"]
    try:
        predictions = model.predict_entities(chunk_text, labels, threshold=0.5)
    except Exception:
        return None

    personnel, parameters = set(), set()
    for p in predictions:
        text = p["text"].strip()
        if p["label"] == "person":
            personnel.add(text)
        elif p["label"] == "process parameter":
            parameters.add(text.lower())

    fields["personnel"] = sorted(personnel)
    fields["parameters"] = sorted(parameters)
    return fields


def _parse_and_validate(response: str) -> dict:
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        return dict(EMPTY_ENTITIES)
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return dict(EMPTY_ENTITIES)

    fields = dict(EMPTY_ENTITIES)
    for key in fields:
        value = data.get(key, [])
        fields[key] = value if isinstance(value, list) else []
    # Guard against hallucinated equipment that isn't in the known fixture list.
    fields["equipment_tags"] = [t for t in fields["equipment_tags"] if t in KNOWN_TAGS]
    return fields


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def extract_entities_for_chunks(chunks: list[dict]) -> dict[str, dict]:
    """Returns {chunk_id: entities}. Only calls the LLM for chunk_ids not already cached."""
    cache = _load_cache()
    changed = False
    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        if chunk_id in cache:
            continue
        cache[chunk_id] = extract_entities(chunk["text"])
        changed = True
    if changed:
        _save_cache(cache)
    return {c["chunk_id"]: cache[c["chunk_id"]] for c in chunks}
