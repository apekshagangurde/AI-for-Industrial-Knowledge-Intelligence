#!/usr/bin/env python3
"""Generate the synthetic "Plant Alpha" dataset (issue #4).

Re-runnable: `python backend/scripts/generate_synthetic_data.py` regenerates
every file in data/synthetic/, overwriting what's there.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.llm_client import complete
from common.plant_alpha import AREAS, EQUIPMENT, PLANT_NAME

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "synthetic"

EQUIPMENT_TABLE = "\n".join(
    f"- {e['tag']}: {e['name']} ({e['type']}), located in {e['area']}" for e in EQUIPMENT
)


def ask_for_docs(kind: str, count: int, instructions: str) -> list[dict]:
    prompt = f"""You are generating a SYNTHETIC (fictional, for a hackathon demo) dataset for
an industrial plant called "{PLANT_NAME}". Do not invent new equipment or areas — use ONLY
this equipment list:

{EQUIPMENT_TABLE}

Plant areas: {', '.join(AREAS)}

Generate exactly {count} {kind}. {instructions}

Return ONLY a JSON array (no markdown fences, no commentary before or after), where each
item has this exact shape:
{{
  "filename_slug": "short-kebab-case-id",
  "date": "YYYY-MM-DD",
  "equipment_tags": ["P-101"],
  "title": "...",
  "body_markdown": "full document body in markdown, 150-350 words"
}}
"""
    response = complete(prompt, system="You output strict JSON and nothing else.")
    return _parse_json_array(response)


def _parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in LLM response:\n{text[:500]}")
    return json.loads(match.group(0))


def write_docs(subdir: str, docs: list[dict], manifest_rows: list[dict], doc_type: str) -> None:
    target = OUT_DIR / subdir
    target.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        filename = f"{doc['date']}_{doc['filename_slug']}.md"
        path = target / filename
        tags = ", ".join(doc["equipment_tags"])
        content = (
            f"# {doc['title']}\n\n"
            f"**Date:** {doc['date']}  \n**Equipment:** {tags}\n\n"
            f"{doc['body_markdown']}\n"
        )
        path.write_text(content)
        manifest_rows.append(
            {
                "filename": f"{subdir}/{filename}",
                "doc_type": doc_type,
                "date": doc["date"],
                "equipment_tags": ";".join(doc["equipment_tags"]),
                "title": doc["title"],
            }
        )
        print(f"  wrote {subdir}/{filename}")


def main() -> None:
    manifest_rows: list[dict] = []

    print("Generating work orders...")
    work_orders = ask_for_docs(
        "maintenance work orders",
        6,
        "Mix routine preventive maintenance and corrective repairs, spread across "
        "Jan-Nov 2024, referencing technician names and hours spent.",
    )
    write_docs("work_orders", work_orders, manifest_rows, "work_order")

    print("Generating inspection reports...")
    inspections = ask_for_docs(
        "equipment inspection reports",
        5,
        "Routine inspections spread across Jan-Nov 2024. At least one inspection on "
        "P-101 should note early signs of mechanical seal wear that gets worse over time.",
    )
    write_docs("inspections", inspections, manifest_rows, "inspection_report")

    print("Generating incident/near-miss reports...")
    incidents = ask_for_docs(
        "incident or near-miss reports",
        4,
        "Exactly two of these must be about P-101 (Feed Pump) mechanical seal failures: "
        "one minor near-miss around June 2024, and one more serious leak/failure around "
        "November 2024 that is clearly a worse recurrence of the same root cause "
        "(reference the earlier one explicitly). The other two should be unrelated "
        "incidents on different equipment.",
    )
    write_docs("incidents", incidents, manifest_rows, "incident")

    print("Generating SOPs...")
    sops = ask_for_docs(
        "standard operating procedures",
        2,
        "One SOP for centrifugal pump startup/shutdown/operation (covering P-101 and "
        "P-102), one for pressure relief valve testing (covering V-301). Dated early "
        "2023 as baseline documents; reference relevant safety regulations generically.",
    )
    write_docs("sops", sops, manifest_rows, "procedure")

    manifest_path = OUT_DIR / "manifest.csv"
    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["filename", "doc_type", "date", "equipment_tags", "title"]
        )
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"\nWrote {len(manifest_rows)} documents. Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
