from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from ingestion.ocr import extract_text, has_text_layer, ocr_image


def test_has_text_layer_true_for_real_text():
    assert has_text_layer("This page has plenty of real extracted text on it.") is True


def test_has_text_layer_false_for_empty_or_near_empty():
    assert has_text_layer(None) is False
    assert has_text_layer("") is False
    assert has_text_layer("   \n  ") is False


def test_extract_text_uses_existing_pdf_layer(tmp_path: Path):
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")  # never opened when a text layer is present

    result = extract_text(pdf_path, pdf_page_text="Real extracted text from the PDF layer.")

    assert result == "Real extracted text from the PDF layer."


def test_extract_text_raises_when_pdf_has_no_text_layer(tmp_path: Path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    with pytest.raises(NotImplementedError):
        extract_text(pdf_path, pdf_page_text="")


def test_extract_text_rejects_unsupported_suffix(tmp_path: Path):
    path = tmp_path / "notes.docx"
    path.write_bytes(b"not really a docx")

    with pytest.raises(ValueError):
        extract_text(path)


def test_ocr_image_extracts_known_text(tmp_path: Path):
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 32)
    image = Image.new("L", (400, 80), color=255)
    ImageDraw.Draw(image).text((10, 10), "HELLO PUMP P-101", fill=0, font=font)
    image_path = tmp_path / "sample.png"
    image.save(image_path)

    text = ocr_image(image_path)

    assert "HELLO" in text.upper()
    assert "P-101" in text.upper()
