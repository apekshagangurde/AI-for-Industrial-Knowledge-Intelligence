"""Parse PDFs and markdown/text docs into structured elements: {doc_id, page, type, text}.

Chunking (#9) and entity extraction (#12) should consume this shape rather
than re-parsing raw files themselves.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import pdfplumber

ElementType = Literal["title", "paragraph", "table"]


def _is_title_line(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 90:
        return False
    if line.endswith((".", ",", ";")):
        return False
    words = line.split()
    if len(words) > 12:
        return False
    return line.isupper() or line.istitle()


def _is_real_table(table: list[list[str | None]]) -> bool:
    # pdfplumber's default table detector frequently misreads footers/page
    # numbers as a 1x1 "table" — require enough structure to be a real one.
    non_empty_cells = sum(1 for row in table for cell in row if cell and cell.strip())
    return len(table) >= 2 and non_empty_cells >= 4


def parse_pdf(path: Path) -> list[dict]:
    doc_id = path.stem
    elements: list[dict] = []

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables():
                if not _is_real_table(table):
                    continue
                rows = [" | ".join(cell or "" for cell in row) for row in table]
                elements.append(
                    {
                        "doc_id": doc_id,
                        "page": page_number,
                        "type": "table",
                        "text": "\n".join(rows),
                    }
                )

            text = page.extract_text() or ""
            for para in re.split(r"\n\s*\n", text):
                para = para.strip()
                if not para:
                    continue
                # A paragraph counts as a title only if EVERY line in it looks
                # like a heading — otherwise a heading-like first line just
                # drags a whole multi-line paragraph into the wrong bucket.
                lines = para.splitlines()
                el_type: ElementType = "title" if all(_is_title_line(l) for l in lines) else "paragraph"
                elements.append(
                    {"doc_id": doc_id, "page": page_number, "type": el_type, "text": para}
                )

    return elements


def parse_markdown(path: Path) -> list[dict]:
    doc_id = path.stem
    text = path.read_text()
    elements: list[dict] = []

    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if lines[0].startswith("#"):
            # Split the heading from its body even when the source glued them
            # onto adjacent lines with no blank line in between — otherwise
            # the whole paragraph gets misclassified as a title.
            elements.append(
                {
                    "doc_id": doc_id,
                    "page": 1,
                    "type": "title",
                    "text": re.sub(r"^#+\s*", "", lines[0]).strip(),
                }
            )
            body = "\n".join(lines[1:]).strip()
            if body:
                elements.append({"doc_id": doc_id, "page": 1, "type": "paragraph", "text": body})
        else:
            elements.append({"doc_id": doc_id, "page": 1, "type": "paragraph", "text": block})

    return elements


def parse_document(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix in (".md", ".txt"):
        return parse_markdown(path)
    raise ValueError(f"Unsupported file type for parsing: {path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sample_paths = [
        repo_root / "data/raw/osha_process_safety_management.pdf",
        repo_root / "data/raw/india_factories_act_1948.pdf",
        repo_root / "data/synthetic/work_orders/2024-01-15_jan-routine-maintenance.md",
    ]
    out_dir = repo_root / "data/processed/parsed_samples"
    out_dir.mkdir(parents=True, exist_ok=True)

    for path in sample_paths:
        elements = parse_document(path)
        out_path = out_dir / f"{path.stem}.json"
        out_path.write_text(json.dumps(elements, indent=2))
        counts: dict[str, int] = {}
        for el in elements:
            counts[el["type"]] = counts.get(el["type"], 0) + 1
        print(f"{path.name}: {len(elements)} elements {counts} -> {out_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
