"""P&ID drawing -> structured JSON (#11).

No custom computer vision: send the drawing image to a vision-capable LLM
(configured via LITELLM_MODEL — e.g. a Groq/Ollama Qwen2-VL or a Claude vision
model) and ask for equipment tags + connections as JSON. Output feeds the
knowledge graph the same way text-extracted entities do.

    python -m ingestion.pid_extractor data/raw/pid_iso10628_sample.png
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import sys
from pathlib import Path

from common.llm_client import vision_complete
from common.observability import observe

SYSTEM_PROMPT = (
    "You read Piping & Instrumentation Diagrams (P&IDs). Extract the visible "
    "equipment and their connections. Output strict JSON only, no commentary."
)

SCHEMA_HINT = """Return a JSON object with exactly these keys:
{
  "equipment_tags": ["P-101", "T-201"],
  "connections": [{"from": "T-201", "to": "P-101", "via": "feed line"}]
}
Only include tags you can actually read in the drawing (formats like P-101,
T-201, HX-401, V-301, C-501). Use empty lists if none are legible."""

EMPTY = {"equipment_tags": [], "connections": []}


def _to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _parse(response: str) -> dict:
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        return dict(EMPTY)
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return dict(EMPTY)
    tags = data.get("equipment_tags", [])
    conns = data.get("connections", [])
    return {
        "equipment_tags": [t for t in tags if isinstance(t, str)] if isinstance(tags, list) else [],
        "connections": [c for c in conns if isinstance(c, dict)] if isinstance(conns, list) else [],
    }


@observe(name="pid.extract")
def extract_pid(image_path: str | Path) -> dict:
    """Returns {equipment_tags, connections} extracted from a P&ID image."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(path)
    prompt = f"{SCHEMA_HINT}\n\nExtract the equipment and connections from this P&ID."
    response = vision_complete(prompt, _to_data_url(path), system=SYSTEM_PROMPT)
    return _parse(response)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        result = extract_pid(arg)
        print(f"{arg}: {json.dumps(result, indent=2)}")
