import pytest
from indexer import chunk_text, extract_text_from_pdf, index_vault


def test_chunk_text_basic():
    words = ["word"] * 600
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 2
    # First chunk: 500 words
    assert len(chunks[0].split()) == 500
    # Second chunk starts 450 words in (500 - 50 overlap), so has 150 words
    assert len(chunks[1].split()) == 150


def test_chunk_text_short_text():
    text = "short text only"
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "short text only"


def test_chunk_text_empty():
    chunks = chunk_text("")
    assert chunks == []
