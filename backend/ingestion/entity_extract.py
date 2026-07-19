"""Extract graph-worthy entities from a chunk's text via the LLM.

Feeds the Neo4j graph writer (#13): equipment tags, parameters, personnel,
dates, and regulation references pulled out of each chunk. Results are
cached on disk keyed by chunk_id, so re-running ingestion doesn't re-spend
LLM calls (and Groq free-tier tokens) on chunks already processed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from common.llm_client import complete
from common.plant_alpha import EQUIPMENT

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = REPO_ROOT / "backend" / "entity_cache.json"

KNOWN_TAGS = {e["tag"] for e in EQUIPMENT}

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
    """Returns {equipment_tags, parameters, personnel, dates, regulation_refs}."""
    prompt = f"{_SCHEMA_HINT}\n\nText:\n{chunk_text}"
    response = complete(prompt, system=SYSTEM_PROMPT)
    return _parse_and_validate(response)


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
