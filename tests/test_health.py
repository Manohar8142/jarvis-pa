from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_incoming_twiml():
    r = TestClient(app).post("/voice/incoming")
    assert r.status_code == 200
    assert "<Stream" in r.text and 'value="screen"' in r.text
