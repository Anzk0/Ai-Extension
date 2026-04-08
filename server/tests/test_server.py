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
