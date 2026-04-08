import pytest
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Point config to a temp path so tests don't need a real vault
    config = {
        "vault_path": str(tmp_path / "vault"),
        "claude_api_key": "test-key",
        "chroma_db_path": str(tmp_path / "chroma_db")
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "vault").mkdir()

    import server
    server.app.config['TESTING'] = True
    with server.app.test_client() as c:
        yield c


def test_status(client):
    res = client.get('/status')
    assert res.status_code == 200
    assert res.get_json() == {'status': 'ok'}
