from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tmba.audio.engine import AudioEngine
from tmba.audio.engine_events import (
    ENGINE_SOURCE_CHANGED,
    ENGINE_STARTED,
    ENGINE_STATE_CHANGED,
)
from tmba.core.event_bus import EventBus


@dataclass
class PipelineStatus:
    state: str = "created"


class FakeManager:
    def __init__(self) -> None:
        self.source = "none"
        self.state = "stopped"
        self.calls: list[tuple[str, Any]] = []
        self.fail_command: str | None = None

    def get_status(self):
        return {
            "source": self.source,
            "state": self.state,
            "volume": 50,
            "registered_sources": ["airplay", "bluetooth", "webradio"],
        }

    def get_pipeline_status(self):
        return {
            "state": "running" if self.state == "playing" else "stopped",
            "output": {"driver": "null"},
        }

    def select_source(self, source: str, *, force: bool = False):
        self.calls.append(("select_source", source, force))
        if self.fail_command == "select_source":
            return {"success": False, "error": "Quellenwechsel fehlgeschlagen"}
        self.source = source
        self.state = "stopped"
        return {"success": True}

    def play(self):
        self.calls.append(("play",))
        if self.fail_command == "play":
            return {"success": False, "error": "Play fehlgeschlagen"}
        self.state = "playing"
        return {"success": True}

    def pause(self):
        self.calls.append(("pause",))
        self.state = "paused"
        return {"success": True}

    def stop(self):
        self.calls.append(("stop",))
        self.state = "stopped"
        return {"success": True}


def test_engine_starts_in_stopped_state():
    engine = AudioEngine(manager=FakeManager(), bus=EventBus())
    status = engine.status()
    assert status["state"] == "stopped"
    assert status["source"] == "none"


def test_start_moves_engine_to_ready():
    engine = AudioEngine(manager=FakeManager(), bus=EventBus())
    result = engine.start()
    assert result["success"] is True
    assert result["engine"]["state"] == "ready"


def test_activate_source_starts_engine_automatically():
    manager = FakeManager()
    engine = AudioEngine(manager=manager, bus=EventBus())
    result = engine.activate_source("webradio")
    assert result["success"] is True
    assert result["engine"]["state"] == "ready"
    assert result["engine"]["source"] == "webradio"
    assert manager.calls == [("select_source", "webradio", False)]


def test_play_and_pause_follow_manager_transport():
    manager = FakeManager()
    engine = AudioEngine(manager=manager, bus=EventBus())
    engine.activate_source("bluetooth")
    assert engine.play()["engine"]["state"] == "playing"
    assert engine.pause()["engine"]["state"] == "paused"


def test_play_without_source_sets_error():
    engine = AudioEngine(manager=FakeManager(), bus=EventBus())
    result = engine.play()
    assert result["success"] is False
    assert result["engine"]["state"] == "error"


def test_stop_releases_source_and_returns_stopped():
    manager = FakeManager()
    engine = AudioEngine(manager=manager, bus=EventBus())
    engine.activate_source("airplay")
    engine.play()
    result = engine.stop()
    assert result["success"] is True
    assert result["engine"]["state"] == "stopped"
    assert result["engine"]["source"] == "none"
    assert ("select_source", "none", False) in manager.calls


def test_manager_failure_sets_engine_error():
    manager = FakeManager()
    manager.fail_command = "select_source"
    engine = AudioEngine(manager=manager, bus=EventBus())
    result = engine.activate_source("webradio")
    assert result["success"] is False
    assert result["engine"]["state"] == "error"
    assert "Quellenwechsel" in result["error"]


def test_engine_publishes_lifecycle_events():
    bus = EventBus()
    events: list[dict[str, Any]] = []
    for name in (ENGINE_STARTED, ENGINE_STATE_CHANGED, ENGINE_SOURCE_CHANGED):
        bus.subscribe(name, events.append)
    engine = AudioEngine(manager=FakeManager(), bus=bus)
    engine.start()
    engine.activate_source("webradio")
    assert any(event["event"] == ENGINE_STARTED for event in events)
    assert any(event["event"] == ENGINE_SOURCE_CHANGED for event in events)


def test_higher_priority_source_replaces_current_source():
    manager = FakeManager()
    engine = AudioEngine(manager=manager, bus=EventBus())
    engine.activate_source("webradio")
    result = engine.activate_source("airplay")
    assert result["success"] is True
    assert result["engine"]["source"] == "airplay"
    assert result["arbitration"]["accepted"] is True


def test_lower_priority_source_does_not_replace_current_source():
    manager = FakeManager()
    engine = AudioEngine(manager=manager, bus=EventBus())
    engine.activate_source("airplay")
    calls_before = list(manager.calls)
    result = engine.activate_source("webradio")
    assert result["success"] is False
    assert result["engine"]["state"] != "error"
    assert result["engine"]["source"] == "airplay"
    assert manager.calls == calls_before
    assert result["arbitration"]["action"] == "reject"


def test_force_allows_lower_priority_source():
    manager = FakeManager()
    engine = AudioEngine(manager=manager, bus=EventBus())
    engine.activate_source("airplay")
    result = engine.activate_source("webradio", force=True)
    assert result["success"] is True
    assert result["engine"]["source"] == "webradio"
    assert result["arbitration"]["forced"] is True


def test_engine_status_exposes_source_priorities():
    engine = AudioEngine(manager=FakeManager(), bus=EventBus())
    status = engine.status()
    assert status["source_priority"] == 0
    assert status["source_priorities"] == {
        "none": 0,
        "dummy": 1,
        "airplay": 30,
        "bluetooth": 20,
        "webradio": 10,
    }
