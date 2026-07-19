#!/usr/bin/env python3
"""Smoke test for #8: OCR the rendered scanned sample and check legibility
against its known ground truth (AC: >70% legible)."""
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_scanned_sample import GROUND_TRUTH, OUT_PATH  # noqa: E402
from ingestion.ocr import ocr_image  # noqa: E402


def main() -> None:
    if not OUT_PATH.exists():
        raise SystemExit(f"{OUT_PATH} not found -- run generate_scanned_sample.py first")

    extracted = ocr_image(OUT_PATH)
    similarity = difflib.SequenceMatcher(None, GROUND_TRUTH, extracted.strip()).ratio() * 100

    print(f"--- OCR output ---\n{extracted}")
    print(f"--- legibility vs ground truth: {similarity:.1f}% ---")

    if similarity < 70:
        raise SystemExit(f"FAIL: legibility {similarity:.1f}% is below the 70% threshold")
    print("PASS")


if __name__ == "__main__":
    main()
