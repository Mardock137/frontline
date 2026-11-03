"""Extract plain text from uploaded documents.

Supported formats (MVP): PDF, DOCX, TXT, Markdown. The right extractor is
picked based on the content-type (primary) or the filename extension
(fallback).
"""

from __future__ import annotations

import io
from pathlib import PurePath

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentError(ValueError):
    """Raised when we cannot extract text from the given file."""


def extract_text(
    data: bytes,
    *,
    content_type: str | None = None,
    filename: str | None = None,
) -> str:
    """Return the plain-text content of a document.

    Args:
        data: Raw bytes of the uploaded file.
        content_type: MIME type (e.g. ``application/pdf``).
        filename: Original filename, used as a fallback when the content
            type is missing or generic (e.g. ``application/octet-stream``).

    Raises:
        UnsupportedDocumentError: If the format is not supported.
    """
    ext = _guess_extension(content_type, filename)

    if ext == "pdf":
        return _extract_pdf(data)
    if ext == "docx":
        return _extract_docx(data)
    if ext in ("txt", "md"):
        return data.decode("utf-8", errors="replace")

    raise UnsupportedDocumentError(
        f"Unsupported document type (content_type={content_type!r}, "
        f"filename={filename!r}). Supported: PDF, DOCX, TXT, Markdown."
    )


def _guess_extension(content_type: str | None, filename: str | None) -> str:
    ct = (content_type or "").lower().split(";")[0].strip()
    mapping = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
        "text/markdown": "md",
        "text/x-markdown": "md",
    }
    if ct in mapping:
        return mapping[ct]

    if filename:
        suffix = PurePath(filename).suffix.lower().lstrip(".")
        if suffix in ("pdf", "docx", "txt", "md", "markdown"):
            return "md" if suffix == "markdown" else suffix

    return ""


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(part.strip() for part in parts if part.strip())


def _extract_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
