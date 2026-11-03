"""Split long text into overlapping chunks for embedding.

MVP strategy: character-based splitting with a soft boundary preference
for paragraph / sentence breaks. Not as precise as a token-based splitter
but fast, dependency-free, and good enough for FAQs, policies and manuals.

Rule of thumb: 1 token ~= 4 characters in English (and most European
languages). 500 tokens ~= 2000 characters.
"""

from __future__ import annotations

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split ``text`` into overlapping chunks.

    Args:
        text: Full document text.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Number of characters shared between consecutive
            chunks (must be smaller than ``chunk_size``).

    Returns:
        A list of non-empty, stripped chunk strings. Returns ``[]`` if the
        input is empty / whitespace.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be in [0, chunk_size)")

    clean = text.strip()
    if not clean:
        return []

    if len(clean) <= chunk_size:
        return [clean]

    chunks: list[str] = []
    start = 0
    text_len = len(clean)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        if end < text_len:
            end = _find_soft_break(clean, start, end)

        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        start = max(end - chunk_overlap, start + 1)

    return chunks


def _find_soft_break(text: str, start: int, end: int) -> int:
    """Try to move ``end`` to the nearest paragraph / sentence break.

    Looks backwards from ``end`` within a small window; if no good break
    is found, keeps the hard boundary.
    """
    window = min(400, (end - start) // 4)
    search_from = max(start + 1, end - window)

    for separator in ("\n\n", ". ", "\n", " "):
        idx = text.rfind(separator, search_from, end)
        if idx != -1:
            return idx + len(separator)
    return end
