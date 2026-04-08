import pytest
from unittest.mock import MagicMock, patch
from claude_client import ask_claude


@pytest.fixture
def mock_anthropic(monkeypatch):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Quicksort works by partitioning.")]
    mock_client.messages.create.return_value = mock_message
    monkeypatch.setattr('claude_client.anthropic.Anthropic', lambda **kwargs: mock_client)
    return mock_client


def test_ask_claude_returns_answer(mock_anthropic):
    chunks = [{'text': 'Quicksort partitions the array.', 'filename': 'sorting.pdf', 'topic': 'Algorithms'}]
    result = ask_claude("How does quicksort work?", chunks, "test-key")
    assert result['answer'] == "Quicksort works by partitioning."
    assert 'sorting.pdf' in result['sources']


def test_ask_claude_includes_chunks_in_prompt(mock_anthropic):
    chunks = [{'text': 'TCP uses handshake.', 'filename': 'tcp.pdf', 'topic': 'Networks'}]
    ask_claude("What is TCP?", chunks, "test-key")
    call_kwargs = mock_anthropic.messages.create.call_args
    system_prompt = call_kwargs.kwargs['system']
    assert 'tcp.pdf' in system_prompt
    assert 'TCP uses handshake.' in system_prompt


def test_ask_claude_no_chunks(mock_anthropic):
    result = ask_claude("What is TCP?", [], "test-key")
    assert result['answer'] == "Quicksort works by partitioning."
    assert result['sources'] == []
    call_kwargs = mock_anthropic.messages.create.call_args
    system_prompt = call_kwargs.kwargs['system']
    assert 'No study materials' in system_prompt
