"""Split parsed elements (parse_docs.parse_document output) into retrieval-sized chunks.

Chunks by section/heading boundaries first, so a section's content stays
together. Falls back to a ~500-token sliding window (with overlap) within a
section, or across the whole doc when it has no headings at all. Tables are
always kept as their own single chunk — a table is never split mid-row.
"""
from __future__ import annotations

TARGET_TOKENS = 500
OVERLAP_TOKENS = 50


def _word_windows(words: list[str], size: int = TARGET_TOKENS, overlap: int = OVERLAP_TOKENS) -> list[list[str]]:
    if not words:
        return []
    step = max(size - overlap, 1)
    windows = []
    i = 0
    while True:
        windows.append(words[i : i + size])
        if i + size >= len(words):
            break
        i += step
    return windows


def _flush_section(doc_id: str, doc_type: str | None, section_title: str | None, paragraphs: list[dict]) -> list[dict]:
    """Turn a section's paragraph elements into one or more text chunks."""
    if not paragraphs:
        return []

    words_with_page: list[tuple[str, int]] = []
    for el in paragraphs:
        for word in el["text"].split():
            words_with_page.append((word, el["page"]))

    windows = _word_windows([w for w, _ in words_with_page])
    pages = [p for _, p in words_with_page]

    chunks = []
    offset = 0
    for window in windows:
        page = pages[offset] if offset < len(pages) else pages[-1]
        chunks.append(
            {
                "doc_id": doc_id,
                "doc_type": doc_type,
                "page": page,
                "section_title": section_title,
                "type": "text",
                "text": " ".join(window),
            }
        )
        offset += max(TARGET_TOKENS - OVERLAP_TOKENS, 1)
    return chunks


def chunk_elements(elements: list[dict], doc_type: str | None = None) -> list[dict]:
    """Chunk one document's parsed elements. Returns chunks with a `chunk_index` added."""
    if not elements:
        return []

    doc_id = elements[0]["doc_id"]
    chunks: list[dict] = []

    current_title: str | None = None
    current_paragraphs: list[dict] = []

    for el in elements:
        if el["type"] == "title":
            chunks.extend(_flush_section(doc_id, doc_type, current_title, current_paragraphs))
            current_paragraphs = []
            current_title = el["text"]
        elif el["type"] == "table":
            # Flush whatever text has accumulated so the table stays its own chunk.
            chunks.extend(_flush_section(doc_id, doc_type, current_title, current_paragraphs))
            current_paragraphs = []
            chunks.append(
                {
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "page": el["page"],
                    "section_title": current_title,
                    "type": "table",
                    "text": el["text"],
                }
            )
        else:  # paragraph
            current_paragraphs.append(el)

    chunks.extend(_flush_section(doc_id, doc_type, current_title, current_paragraphs))

    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i
        chunk["chunk_id"] = f"{doc_id}::{i}"

    return chunks
