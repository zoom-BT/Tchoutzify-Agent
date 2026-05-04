import pytest
import json
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    with patch('server.SpotifyController'), \
         patch('server.TTSEngine'):
        from server import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client


def test_health_returns_ok(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'


def test_speak_returns_ok(client):
    response = client.post('/speak',
        data=json.dumps({'text': 'Bonjour', 'type': 'intro'}),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_speak_requires_text(client):
    response = client.post('/speak',
        data=json.dumps({}),
        content_type='application/json'
    )
    assert response.status_code == 400
