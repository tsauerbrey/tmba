from typing import Any

from tmba.audio.manager import AudioManager


class FakeSource:
    def __init__(
        self,
        *,
        available: bool = True,
        stop_success: bool = True,
    ) -> None:
        self.available = available
        self.stop_success = stop_success
        self.commands: list[str] = []
        self.volume = 50
        self.playback_status = "idle"

    def get_status(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "playback_status": self.playback_status,
        }

    def play(self) -> dict[str, Any]:
        self.commands.append("play")
        self.playback_status = "playing"
        return {"success": True}

    def pause(self) -> dict[str, Any]:
        self.commands.append("pause")
        self.playback_status = "paused"
        return {"success": True}

    def stop(self) -> dict[str, Any]:
        self.commands.append("stop")

        if not self.stop_success:
            return {
                "success": False,
                "error": "Stop fehlgeschlagen",
            }

        self.playback_status = "stopped"
        return {"success": True}

    def previous(self) -> dict[str, Any]:
        self.commands.append("previous")
        return {"success": True}

    def next(self) -> dict[str, Any]:
        self.commands.append("next")
        return {"success": True}

    def set_volume(self, volume: int) -> dict[str, Any]:
        self.commands.append("set_volume")
        self.volume = volume
        return {
            "success": True,
            "volume": volume,
        }


def create_manager() -> tuple[AudioManager, FakeSource, FakeSource]:
    manager = AudioManager()
    webradio = FakeSource()
    bluetooth = FakeSource()

    manager.register_source("webradio", webradio)
    manager.register_source("bluetooth", bluetooth)

    return manager, webradio, bluetooth


def test_initial_state():
    manager = AudioManager()

    status = manager.get_status()

    assert status["source"] == "none"
    assert status["state"] == "stopped"
    assert status["volume"] == 50


def test_source_switch_stops_previous_source():
    manager, webradio, _bluetooth = create_manager()

    first = manager.select_source("webradio")
    second = manager.select_source("bluetooth")

    assert first["success"] is True
    assert second["success"] is True
    assert webradio.commands == ["stop"]
    assert manager.get_status()["source"] == "bluetooth"


def test_transport_is_routed_to_active_source():
    manager, webradio, _bluetooth = create_manager()

    manager.select_source("webradio")
    result = manager.play()

    assert result["success"] is True
    assert webradio.commands == ["play"]
    assert manager.get_status()["state"] == "playing"


def test_volume_is_normalized_and_applied_to_master():
    manager, webradio, _bluetooth = create_manager()

    manager.select_source("webradio")
    result = manager.set_volume(140)

    assert result["success"] is True
    assert result["volume"] == 100
    assert webradio.volume == 50
    assert "set_volume" not in webradio.commands
    assert manager.get_status()["volume"] == 100


def test_failed_stop_blocks_source_change():
    manager = AudioManager()
    failing_source = FakeSource(stop_success=False)
    target_source = FakeSource()

    manager.register_source("webradio", failing_source)
    manager.register_source("bluetooth", target_source)

    manager.select_source("webradio")
    result = manager.select_source("bluetooth")

    assert result["success"] is False
    assert manager.get_status()["state"] == "error"
    assert manager.get_status()["source"] == "webradio"


def test_unknown_source_is_rejected():
    manager = AudioManager()

    try:
        manager.select_source("cassette")
    except ValueError as error:
        assert "Unbekannte Audioquelle" in str(error)
    else:
        raise AssertionError("ValueError wurde erwartet.")
