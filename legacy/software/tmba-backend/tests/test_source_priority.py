from fastapi.testclient import TestClient

from tmba.main import app


client = TestClient(app)


def test_source_priority_chain() -> None:
    """
    Prüft die vollständige Quellenpriorität:

    Webradio -> Bluetooth -> AirPlay -> Bluetooth -> Webradio
    """

    # Alle simulierten Sitzungen zunächst beenden.
    client.post("/airplay/session/end")
    client.post("/bluetooth/session/end")

    # Webradio aktivieren.
    response = client.post("/webradio/session/start")
    assert response.status_code == 200

    response = client.post(
        "/webradio/metadata",
        json={
            "title": "Webradio Test",
            "artist": "Live",
            "album": "Webradio",
            "cover_url": "",
            "duration": 0,
            "elapsed": 10,
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/webradio/playback-status",
        json={"status": "playing"},
    )
    assert response.status_code == 200

    status = client.get("/status").json()

    assert status["source"] == "webradio"
    assert status["status"] == "playing"
    assert status["track"]["title"] == "Webradio Test"

    # Bluetooth hat höhere Priorität als Webradio.
    response = client.post("/bluetooth/session/start")
    assert response.status_code == 200

    status = client.get("/status").json()

    assert status["source"] == "bluetooth"
    assert status["status"] == "idle"

    # AirPlay hat höhere Priorität als Bluetooth.
    response = client.post("/airplay/session/start")
    assert response.status_code == 200

    status = client.get("/status").json()

    assert status["source"] == "airplay"
    assert status["status"] == "idle"

    # AirPlay endet: Bluetooth muss zurückkehren.
    response = client.post("/airplay/session/end")
    assert response.status_code == 200

    status = client.get("/status").json()

    assert status["source"] == "bluetooth"
    assert status["status"] == "idle"

    # Bluetooth endet: Webradio muss zurückkehren.
    response = client.post("/bluetooth/session/end")
    assert response.status_code == 200

    status = client.get("/status").json()

    assert status["source"] == "webradio"
    assert status["status"] == "playing"
    assert status["track"]["title"] == "Webradio Test"