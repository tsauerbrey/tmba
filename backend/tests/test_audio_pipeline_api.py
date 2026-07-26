from fastapi.testclient import TestClient

from tmba.audio.manager import audio_manager
from tmba.main import app

client = TestClient(app)

def test_pipeline_endpoint_returns_pipeline_status():
    response = client.get("/audio/pipeline")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] in {"created", "ready", "running", "stopped", "error"}
    assert payload["stage_count"] == 6
    assert payload["enabled_stage_count"] >= 1
    assert isinstance(payload["output"], dict)
    assert isinstance(payload["stages"], list)
    assert isinstance(payload["config"], dict)

def test_pipeline_endpoint_contains_output_stage():
    response = client.get("/audio/pipeline")
    assert response.status_code == 200
    assert response.json()["stages"][-1]["stage_type"] == "output"

def test_pipeline_endpoint_returns_503_on_status_failure(monkeypatch):
    def fail_status():
        raise RuntimeError("Testfehler")
    monkeypatch.setattr(audio_manager, "get_pipeline_status", fail_status)
    response = client.get("/audio/pipeline")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["success"] is False
    assert "Testfehler" in detail["error"]

def test_root_lists_pipeline_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["audio_pipeline"] == "/audio/pipeline"
