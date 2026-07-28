from fastapi.testclient import TestClient

from tmba.audio.engine import audio_engine
from tmba.main import app

client = TestClient(app)


def test_engine_status_endpoint():
    response = client.get("/audio/engine")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] in {
        "stopped", "starting", "ready", "playing", "paused", "stopping", "error"
    }
    assert "pipeline_state" in payload
    assert "output_driver" in payload


def test_engine_start_endpoint(monkeypatch):
    monkeypatch.setattr(
        audio_engine,
        "start",
        lambda: {"success": True, "engine": {"state": "ready"}},
    )
    response = client.post("/audio/engine/start")
    assert response.status_code == 200
    assert response.json()["engine"]["state"] == "ready"


def test_engine_source_endpoint_rejects_unknown_source():
    response = client.post(
        "/audio/engine/source",
        json={"source": "cassette"},
    )
    assert response.status_code == 400


def test_root_lists_engine_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["audio_engine"] == "/audio/engine"
