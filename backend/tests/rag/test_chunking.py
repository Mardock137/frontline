"""Tests for the text chunker."""

import pytest

from rag.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []


def test_short_text_returns_single_chunk():
    text = "Just a short FAQ entry."
    assert chunk_text(text) == [text]


def test_long_text_is_split_with_overlap():
    paragraph = ("Sentence about widgets. " * 20).strip()
    text = "\n\n".join([paragraph] * 10)

    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)

    assert len(chunks) > 1
    assert all(len(c) <= 500 + 1 for c in chunks)
    assert all(c.strip() == c for c in chunks)


def test_chunks_have_overlap_between_consecutive_pieces():
    text = "".join(f"word{i} " for i in range(500))

    chunks = chunk_text(text, chunk_size=400, chunk_overlap=80)

    assert len(chunks) >= 2
    tail = chunks[0][-50:].strip()
    assert tail[:10] in chunks[1] or chunks[0][-20:].split()[-1] in chunks[1]


def test_invalid_chunk_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=100, chunk_overlap=-1)


def test_invalid_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=0)


def test_prefers_paragraph_boundaries():
    para_a = "A" * 300
    para_b = "B" * 300
    text = f"{para_a}\n\n{para_b}"

    chunks = chunk_text(text, chunk_size=400, chunk_overlap=50)

    assert chunks[0].strip() == para_a
