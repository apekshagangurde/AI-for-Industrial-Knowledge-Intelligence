#!/usr/bin/env python3
"""Smoke test for #12: run entity extraction on 10 sample chunks and check
equipment-tag recall against what's literally in the text (AC: >80%)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.chunker import chunk_elements  # noqa: E402
from ingestion.entity_extract import KNOWN_TAGS, extract_entities_for_chunks  # noqa: E402
from ingestion.parse_docs import parse_document  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = REPO_ROOT / "data" / "synthetic"


def main() -> None:
    chunks: list[dict] = []
    for md_path in sorted(SYNTHETIC_DIR.rglob("*.md")):
        elements = parse_document(md_path)
        chunks.extend(chunk_elements(elements))
        if len(chunks) >= 10:
            break
    sample = chunks[:10]

    results = extract_entities_for_chunks(sample)

    correct = 0
    checked = 0
    for chunk in sample:
        mentioned = {tag for tag in KNOWN_TAGS if tag in chunk["text"]}
        extracted = set(results[chunk["chunk_id"]]["equipment_tags"])
        print(f"{chunk['chunk_id']}")
        print(f"  mentioned in text: {sorted(mentioned) or '(none)'}")
        print(f"  extracted:         {sorted(extracted) or '(none)'}")
        if mentioned:
            checked += 1
            if mentioned <= extracted:
                correct += 1

    if checked:
        recall = 100 * correct / checked
        print(f"\nEquipment tag recall: {correct}/{checked} chunks ({recall:.0f}%)")
        if recall < 80:
            raise SystemExit("FAIL: recall below the 80% threshold")
        print("PASS")
    else:
        print("\nNo chunks in the sample mentioned a known equipment tag.")


if __name__ == "__main__":
    main()
