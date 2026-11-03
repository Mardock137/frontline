"""Tests for the text extraction module."""

import io

import pytest
from docx import Document as DocxDocument

from rag.text_extraction import UnsupportedDocumentError, extract_text


def _build_docx_bytes(paragraphs: list[str]) -> bytes:
    buffer = io.BytesIO()
    doc = DocxDocument()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(buffer)
    return buffer.getvalue()


def test_extract_plain_text():
    data = "Hello, world!\nSecond line.".encode("utf-8")
    assert extract_text(data, content_type="text/plain", filename="a.txt") == (
        "Hello, world!\nSecond line."
    )


def test_extract_markdown_by_filename():
    data = b"# Title\n\nParagraph."
    out = extract_text(data, content_type=None, filename="notes.md")
    assert "Title" in out


def test_extract_docx_roundtrip():
    data = _build_docx_bytes(["First paragraph.", "Second paragraph."])
    text = extract_text(
        data,
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename="doc.docx",
    )
    assert "First paragraph." in text
    assert "Second paragraph." in text


def test_extract_docx_by_extension_fallback():
    data = _build_docx_bytes(["Body."])
    text = extract_text(
        data, content_type="application/octet-stream", filename="x.docx"
    )
    assert "Body." in text


def test_unsupported_raises():
    with pytest.raises(UnsupportedDocumentError):
        extract_text(b"binary", content_type="image/png", filename="a.png")
