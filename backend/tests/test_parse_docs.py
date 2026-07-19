from pathlib import Path

from ingestion.parse_docs import _is_real_table, parse_markdown


def test_markdown_heading_glued_to_body_is_split(tmp_path: Path):
    """Regression test: a `## Heading` immediately followed by body text on
    the next line (no blank line) must not swallow the whole paragraph into
    the title element."""
    md_path = tmp_path / "doc.md"
    md_path.write_text("# Title\n\n## Subheading\nBody text right after the heading.\n")

    elements = parse_markdown(md_path)

    assert elements[0] == {"doc_id": "doc", "page": 1, "type": "title", "text": "Title"}
    assert elements[1]["type"] == "title"
    assert elements[1]["text"] == "Subheading"
    assert elements[2]["type"] == "paragraph"
    assert elements[2]["text"] == "Body text right after the heading."


def test_markdown_plain_paragraph_is_not_a_title(tmp_path: Path):
    md_path = tmp_path / "doc.md"
    md_path.write_text("Just a plain paragraph, no heading.\n")

    elements = parse_markdown(md_path)

    assert elements == [
        {
            "doc_id": "doc",
            "page": 1,
            "type": "paragraph",
            "text": "Just a plain paragraph, no heading.",
        }
    ]


def test_is_real_table_rejects_single_cell_false_positives():
    assert _is_real_table([["", "iii", ""]]) is False


def test_is_real_table_accepts_structured_table():
    assert _is_real_table([["Tag", "Type"], ["P-101", "Pump"], ["V-301", "Valve"]]) is True
