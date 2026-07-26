from __future__ import annotations

from dataclasses import replace

import pytest

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources import (
    AudioSource,
    AudioSourceRegistry,
    SourceCapabilities,
    SourceLifecycleState,
    SourceStatus,
)


class FakeSource(AudioSource):
    def __init__(self, source: EngineSource = EngineSource.WEBRADIO):
        self._source = source
        self._status = SourceStatus(
            source=source,
            state=SourceLifecycleState.DISCONNECTED,
            connected=False,
            active=False,
        )

    @property
    def source(self) -> EngineSource:
        return self._source

    @property
    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(provides_pcm=True)

    def connect(self) -> SourceStatus:
        self._status = replace(
            self._status,
            state=SourceLifecycleState.READY,
            connected=True,
        )
        return self._status

    def disconnect(self) -> SourceStatus:
        self._status = replace(
            self._status,
            state=SourceLifecycleState.DISCONNECTED,
            connected=False,
            active=False,
        )
        return self._status

    def start(self) -> SourceStatus:
        if not self._status.connected:
            self.connect()
        self._status = replace(
            self._status,
            state=SourceLifecycleState.PLAYING,
            active=True,
        )
        return self._status

    def stop(self) -> SourceStatus:
        self._status = replace(
            self._status,
            state=SourceLifecycleState.READY,
            active=False,
        )
        return self._status

    def pause(self) -> SourceStatus:
        self._status = replace(
            self._status,
            state=SourceLifecycleState.PAUSED,
            active=True,
        )
        return self._status

    def resume(self) -> SourceStatus:
        return self.start()

    def status(self) -> SourceStatus:
        return self._status


def test_source_status_serializes_enum_values_and_copies_data():
    metadata = {"title": "Test"}
    details = {"buffered_bytes": 1024}
    status = SourceStatus(
        source=EngineSource.AIRPLAY,
        state=SourceLifecycleState.PLAYING,
        connected=True,
        active=True,
        metadata=metadata,
        details=details,
    )

    result = status.to_dict()

    assert result["source"] == "airplay"
    assert result["state"] == "playing"
    assert result["metadata"] == metadata
    assert result["details"] == details
    assert result["metadata"] is not metadata
    assert result["details"] is not details


def test_source_capabilities_have_stable_defaults():
    result = SourceCapabilities().to_dict()
    assert result == {
        "can_pause": True,
        "can_resume": True,
        "provides_pcm": False,
        "provides_metadata": True,
        "externally_controlled": False,
    }


def test_source_lifecycle_can_be_implemented_consistently():
    source = FakeSource()

    assert source.connect().state is SourceLifecycleState.READY
    assert source.start().state is SourceLifecycleState.PLAYING
    assert source.pause().state is SourceLifecycleState.PAUSED
    assert source.resume().state is SourceLifecycleState.PLAYING
    assert source.stop().state is SourceLifecycleState.READY
    assert source.disconnect().state is SourceLifecycleState.DISCONNECTED


def test_registry_registers_and_resolves_source():
    source = FakeSource()
    registry = AudioSourceRegistry([source])

    assert registry.get("webradio") is source
    assert registry.require(EngineSource.WEBRADIO) is source
    assert registry.names() == ("webradio",)


def test_registry_rejects_duplicate_without_explicit_replace():
    registry = AudioSourceRegistry([FakeSource()])

    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(FakeSource())


def test_registry_can_replace_and_unregister_source():
    first = FakeSource()
    replacement = FakeSource()
    registry = AudioSourceRegistry([first])

    registry.register(replacement, replace=True)

    assert registry.require("webradio") is replacement
    assert registry.unregister("webradio") is replacement
    assert registry.get("webradio") is None


def test_registry_rejects_none_and_unknown_sources():
    registry = AudioSourceRegistry()

    with pytest.raises(ValueError, match="Pseudoquelle"):
        registry.register(FakeSource(EngineSource.NONE))

    with pytest.raises(ValueError, match="Unbekannte Audioquelle"):
        registry.get("cassette")


def test_registry_require_reports_missing_implementation():
    with pytest.raises(LookupError, match="keine AudioSource"):
        AudioSourceRegistry().require("bluetooth")


def test_registry_statuses_uses_normalized_status_contract():
    source = FakeSource(EngineSource.BLUETOOTH)
    source.connect()
    registry = AudioSourceRegistry([source])

    statuses = registry.statuses()

    assert statuses["bluetooth"]["source"] == "bluetooth"
    assert statuses["bluetooth"]["state"] == "ready"
