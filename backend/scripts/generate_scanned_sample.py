#!/usr/bin/env python3
"""Render a "scanned" inspection form (flat image, no text layer) for #8's OCR test.

Every other raw doc in data/raw/ is a real PDF/SVG with a text layer already,
so there's nothing to actually exercise OCR against. This renders known
ground-truth text onto a plain image -- a stand-in for a scanned paper form
-- so ocr.py has something real to be tested on.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = REPO_ROOT / "data" / "raw" / "scanned_inspection_form_sample.png"

GROUND_TRUTH = """EQUIPMENT INSPECTION REPORT

Plant: Plant Alpha
Equipment Tag: P-101
Equipment Type: Centrifugal Pump
Inspector: Priya Sharma
Date: 2024-05-15

Findings:
Minor vibration noted near the pump coupling.
Seal housing shows early signs of wear and
minor fluid seepage. Recommend mechanical seal
replacement within the next 60 days.

Status: Monitor
Next Inspection Due: 2024-08-15"""


def main() -> None:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    lines = GROUND_TRUTH.split("\n")
    line_height = 40
    width, height = 900, line_height * len(lines) + 80

    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)
    y = 40
    for line in lines:
        draw.text((40, y), line, fill=0, font=font)
        y += line_height

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
