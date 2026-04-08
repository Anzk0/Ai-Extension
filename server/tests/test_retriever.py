import pytest
from indexer import index_vault
from retriever import retrieve_chunks


@pytest.fixture
def indexed_vault(tmp_vault, tmp_chroma):
    index_vault(tmp_vault, tmp_chroma)
    return tmp_chroma


def test_retrieve_returns_chunks(indexed_vault):
    chunks = retrieve_chunks("sorting algorithms", "Algorithms", indexed_vault)
    assert len(chunks) > 0
    assert 'text' in chunks[0]
    assert 'filename' in chunks[0]
    assert 'topic' in chunks[0]


def test_retrieve_respects_topic_filter(indexed_vault):
    chunks = retrieve_chunks("connections", "Networks", indexed_vault)
    assert all(c['topic'] == 'Networks' for c in chunks)


def test_retrieve_returns_empty_for_unknown_topic(indexed_vault):
    chunks = retrieve_chunks("anything", "NonExistentTopic", indexed_vault)
    assert chunks == []
