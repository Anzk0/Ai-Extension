from indexer import chunk_text, extract_text_from_pdf, index_vault
import chromadb


def test_chunk_text_basic():
    words = ["word"] * 600
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 2
    assert len(chunks[0].split()) == 500
    assert len(chunks[1].split()) == 150


def test_chunk_text_short_text():
    text = "short text only"
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "short text only"


def test_chunk_text_empty():
    chunks = chunk_text("")
    assert chunks == []


def test_chunk_text_invalid_overlap():
    import pytest
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("some text", chunk_size=50, overlap=50)


def test_extract_text_from_pdf(tmp_vault):
    import os
    pdf_path = os.path.join(tmp_vault, "Algorithms", "sorting.pdf")
    text = extract_text_from_pdf(pdf_path)
    assert "Quicksort" in text
    assert len(text) > 50


def test_index_vault_creates_entries(tmp_vault, tmp_chroma):
    index_vault(tmp_vault, tmp_chroma)
    client = chromadb.PersistentClient(path=tmp_chroma)
    collection = client.get_collection('vault')
    count = collection.count()
    assert count > 0


def test_index_vault_stores_topic_metadata(tmp_vault, tmp_chroma):
    index_vault(tmp_vault, tmp_chroma)
    client = chromadb.PersistentClient(path=tmp_chroma)
    collection = client.get_collection('vault')
    results = collection.get(where={'topic': 'Algorithms'})
    assert len(results['ids']) > 0
    assert all(m['topic'] == 'Algorithms' for m in results['metadatas'])
