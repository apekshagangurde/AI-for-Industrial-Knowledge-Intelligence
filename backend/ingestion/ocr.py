"""OCR for scanned/image documents with no text layer.

parse_docs.parse_pdf() already extracts real text layers directly, so this
module only kicks in for images (PNG/JPG scans) or a PDF page that turns out
to have no usable text layer.
"""
from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff")


def ocr_image(path: Path) -> str:
    image = Image.open(path)
    return pytesseract.image_to_string(image)


def has_text_layer(pdf_page_text: str | None) -> bool:
    """True if a PDF page's extracted text layer looks real, not empty/near-empty."""
    return bool(pdf_page_text and len(pdf_page_text.strip()) > 20)


def extract_text(path: Path, pdf_page_text: str | None = None) -> str:
    """Route to OCR only when there's no usable text layer.

    Images are always OCR'd. For a PDF page, pass its parse_docs-extracted
    text in `pdf_page_text` — if that looks empty, the caller should
    rasterize the page to an image and call ocr_image() on it instead.
    """
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return ocr_image(path)
    if suffix == ".pdf":
        if has_text_layer(pdf_page_text):
            return pdf_page_text or ""
        raise NotImplementedError(
            "PDF page has no text layer -- rasterize the page to an image "
            "and pass it to ocr_image() instead."
        )
    raise ValueError(f"Unsupported file type for OCR routing: {path}")
