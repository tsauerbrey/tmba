from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tmba.audio.manager import AudioManager


class FakeSource:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.playback_status = "idle"

    def get_status(self) -> dict[str, Any]:
        return {"playback_status": self.playback_status}

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
        self.playback_status = "stopped"
        return {"success": True}

    def previous(self) -> dict[str, Any]:
        self.commands.append("previous")
        return {"success": True}

    def next(self) -> dict[str, Any]:
        self.commands.append("next")
        return {"success": True}

    def set_volume(self, volume: int) -> dict[str, Any]:
        return {"success": True, "volume": volume}


@dataclass
class FakePipelineStatus:
    state: str = "created"


class FakePipeline:
    def __init__(
        self,
        *,
        fail_start: bool = False,
        fail_stop: bool = False,
    ) -> None:
        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.start_calls = 0
        self.stop_calls = 0
        self.current_state = "created"

    def start(self) -> None:
        self.start_calls += 1
        if self.fail_start:
            raise RuntimeError("Pipeline-Start fehlgeschlagen")
        self.current_state = "running"

    def stop(self) -> None:
        self.stop_calls += 1
        if self.fail_stop:
            raise RuntimeError("Pipeline-Stopp fehlgeschlagen")
        self.current_state = "stopped"

    def status(self) -> FakePipelineStatus:
        return FakePipelineStatus(state=self.current_state)


def create_manager(
    pipeline: FakePipeline | None = None,
) -> tuple[AudioManager, FakeSource, FakePipeline]:
    selected_pipeline = pipeline or FakePipeline()
    manager = AudioManager(pipeline=selected_pipeline)
    source = FakeSource()
    manager.register_source("webradio", source)
    manager.select_source("webradio")
    return manager, source, selected_pipeline


def test_manager_uses_injected_pipeline() -> None:
    pipeline = FakePipeline()
    manager = AudioManager(pipeline=pipeline)

    assert manager.pipeline is pipeline


def test_successful_play_starts_pipeline() -> None:
    manager, source, pipeline = create_manager()

    result = manager.play()

    assert result["success"] is True
    assert source.commands == ["play"]
    assert pipeline.start_calls == 1
    assert manager.get_status()["state"] == "playing"


def test_stop_stops_source_and_pipeline() -> None:
    manager, source, pipeline = create_manager()
    manager.play()

    result = manager.stop()

    assert result["success"] is True
    assert source.commands == ["play", "stop"]
    assert pipeline.stop_calls == 1
    assert manager.get_status()["state"] == "stopped"


def test_stop_without_source_still_stops_pipeline() -> None:
    pipeline = FakePipeline()
    manager = AudioManager(pipeline=pipeline)

    result = manager.stop()

    assert result["success"] is True
    assert pipeline.stop_calls == 1


def test_pipeline_start_failure_rolls_back_source() -> None:
    pipeline = FakePipeline(fail_start=True)
    manager, source, _pipeline = create_manager(pipeline)

    result = manager.play()

    assert result["success"] is False
    assert source.commands == ["play", "stop"]
    assert pipeline.start_calls == 1
    assert manager.get_status()["state"] == "error"
    assert "Pipeline-Start fehlgeschlagen" in result["error"]


def test_pipeline_stop_failure_sets_manager_error() -> None:
    pipeline = FakePipeline(fail_stop=True)
    manager, source, _pipeline = create_manager(pipeline)

    result = manager.stop()

    assert result["success"] is False
    assert source.commands == ["stop"]
    assert manager.get_status()["state"] == "error"
    assert "Pipeline-Stopp fehlgeschlagen" in result["error"]


def test_source_change_stops_pipeline() -> None:
    manager, source, pipeline = create_manager()
    bluetooth = FakeSource()
    manager.register_source("bluetooth", bluetooth)
    manager.play()

    result = manager.select_source("bluetooth")

    assert result["success"] is True
    assert source.commands == ["play", "stop"]
    assert pipeline.stop_calls == 1
    assert manager.get_status()["source"] == "bluetooth"
    assert manager.get_status()["state"] == "stopped"


def test_select_none_stops_pipeline() -> None:
    manager, source, pipeline = create_manager()
    manager.play()

    result = manager.select_source("none")

    assert result["success"] is True
    assert source.commands == ["play", "stop"]
    assert pipeline.stop_calls == 1
    assert manager.get_status()["source"] == "none"


def test_pipeline_status_is_available_without_rest_api() -> None:
    manager, _source, pipeline = create_manager()
    pipeline.current_state = "ready"

    status = manager.get_pipeline_status()

    assert status == {"state": "ready"}
