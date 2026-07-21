"""Compliance check (#27): map a procedure against a regulation using the RAG
substrate, and have the LLM flag gaps between what the regulation requires and
what the procedure actually does.

Reuses retrieval + generation; the two documents are pulled from Chroma by
doc_id and fed to a preset gap-analysis prompt.
"""
from __future__ import annotations

import json
import re

from common.llm_client import complete_json
from common.observability import observe
from ingestion.embed_store import get_collection

COMPLIANCE_SYSTEM_PROMPT = (
    "You are a compliance auditor for an industrial plant. Compare the PROCEDURE "
    "against the REGULATION. Identify concrete gaps where the procedure fails to meet, "
    "or does not address, a requirement of the regulation. Output strict JSON only:\n"
    '{"gaps": [{"requirement": "...", "finding": "...", "severity": "high|medium|low"}], '
    '"summary": "...", "compliant": true|false}\n'
    "Use an empty gaps list and compliant=true if the procedure adequately meets the "
    "regulation. Base every finding on the provided text — do not invent requirements."
)


def _doc_text(doc_id: str, limit_chars: int = 6000) -> str:
    """Concatenate a document's chunks (ordered) from Chroma into one string."""
    collection = get_collection()
    data = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    if not data["ids"]:
        return ""
    ordered = sorted(
        zip(data["ids"], data["documents"]),
        key=lambda pair: int(pair[0].split("::")[-1]) if "::" in pair[0] else 0,
    )
    return "\n".join(text for _, text in ordered)[:limit_chars]


def _parse(response: str) -> dict:
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        return {"gaps": [], "summary": response[:500], "compliant": None}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"gaps": [], "summary": response[:500], "compliant": None}
    data.setdefault("gaps", [])
    data.setdefault("summary", "")
    data.setdefault("compliant", None)
    return data


@observe(name="compliance.check")
def check_compliance(procedure_id: str, regulation_id: str) -> dict:
    """Returns {procedure_id, regulation_id, gaps, summary, compliant}."""
    procedure = _doc_text(procedure_id)
    regulation = _doc_text(regulation_id)

    if not procedure or not regulation:
        missing = procedure_id if not procedure else regulation_id
        return {
            "procedure_id": procedure_id,
            "regulation_id": regulation_id,
            "gaps": [],
            "summary": f"Document '{missing}' was not found in the knowledge base.",
            "compliant": None,
        }

    prompt = f"REGULATION ({regulation_id}):\n{regulation}\n\nPROCEDURE ({procedure_id}):\n{procedure}"
    result = _parse(complete_json(prompt, system=COMPLIANCE_SYSTEM_PROMPT))
    result["procedure_id"] = procedure_id
    result["regulation_id"] = regulation_id
    return result
