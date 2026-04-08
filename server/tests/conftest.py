import pytest
import tempfile
import os
import fitz


@pytest.fixture
def tmp_vault(tmp_path):
    """Creates a temporary vault with two topics, each containing one PDF."""
    topic_a = tmp_path / "Algorithms"
    topic_b = tmp_path / "Networks"
    topic_a.mkdir()
    topic_b.mkdir()

    def make_pdf(path, text):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), text)
        doc.save(str(path))
        doc.close()

    make_pdf(topic_a / "sorting.pdf", "Quicksort divides a list into two halves around a pivot element. " * 20)
    make_pdf(topic_b / "tcp.pdf", "TCP uses a three-way handshake to establish connections reliably. " * 20)
    return str(tmp_path)


@pytest.fixture
def tmp_chroma(tmp_path):
    return str(tmp_path / "chroma_db")
