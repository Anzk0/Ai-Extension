import pytest
import json


@pytest.fixture
def client(tmp_path, monkeypatch):
    config = {
        "vault_path": str(tmp_path / "vault"),
        "claude_api_key": "test-key",
        "chroma_db_path": str(tmp_path / "chroma_db")
    }
    config_path = str(tmp_path / "config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f)
    (tmp_path / "vault").mkdir()

    import server
    monkeypatch.setattr(server, 'load_config', lambda: json.loads(open(config_path).read()))
    server.app.config['TESTING'] = True
    with server.app.test_client() as c:
        yield c


def test_status(client):
    res = client.get('/status')
    assert res.status_code == 200
    assert res.get_json() == {'status': 'ok'}


def test_topics(client, tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "Algorithms").mkdir(parents=True)
    (vault / "Networks").mkdir()
    (vault / "loose_file.pdf").write_text("")  # Not a dir — should be ignored

    res = client.get('/topics')
    assert res.status_code == 200
    data = res.get_json()
    assert set(data['topics']) == {'Algorithms', 'Networks'}


def test_ask_returns_answer(client, monkeypatch):
    monkeypatch.setattr('server.retrieve_chunks', lambda q, t, p, **kw: [
        {'text': 'Quicksort partitions.', 'filename': 'sorting.pdf', 'topic': 'Algorithms'}
    ])
    monkeypatch.setattr('server.ask_claude', lambda q, c, k: {
        'answer': 'Quicksort partitions the array.',
        'sources': ['sorting.pdf']
    })

    res = client.post('/ask', json={'question': 'How does quicksort work?', 'topic': 'Algorithms'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['answer'] == 'Quicksort partitions the array.'
    assert 'sorting.pdf' in data['sources']


def test_ask_missing_fields(client):
    res = client.post('/ask', json={'question': 'What is TCP?'})
    assert res.status_code == 400
    assert 'error' in res.get_json()
