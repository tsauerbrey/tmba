from __future__ import annotations

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources.airplay_runtime import AirPlayRuntimeReport
from tmba.audio.sources.airplay_source import AirPlaySource
from tmba.audio.sources.base import SourceLifecycleState
from tmba.audio.sources.service_process import ServiceRuntimeState, ServiceSnapshot


class AirPlayController:
    def __init__(self): self.running = False
    def inspect(self, name):
        return ServiceSnapshot(name, ServiceRuntimeState.ACTIVE if self.running else ServiceRuntimeState.INACTIVE, "running" if self.running else "dead", 42 if self.running else None)
    def start(self, name): self.running = True; return self.inspect(name)
    def stop(self, name): self.running = False; return self.inspect(name)
    def restart(self, name): self.running = True; return self.inspect(name)


class ReadyRuntimeInspector:
    def inspect(self, config):
        return AirPlayRuntimeReport(
            ready=True,
            binary_found=True,
            config_found=True,
            service_available=True,
            avahi_active=True,
            alsa_device_found=True,
            binary_path="/usr/bin/shairport-sync",
            config_path=config.config_path,
        )


def build_source():
    return AirPlaySource(
        controller=AirPlayController(),
        runtime_inspector=ReadyRuntimeInspector(),
    )


def test_airplay_adapter_has_stable_identity_and_capabilities():
    source = build_source()
    assert source.source is EngineSource.AIRPLAY
    assert source.name == "AirPlay"
    assert source.service_name == "shairport-sync.service"
    assert source.capabilities.externally_controlled is True
    assert source.capabilities.can_pause is False


def test_airplay_adapter_starts_and_stops_shairport_service():
    source = build_source()
    started = source.start()
    assert started.state is SourceLifecycleState.READY
    assert started.active is True
    stopped = source.stop()
    assert stopped.active is False
    assert stopped.connected is True


def test_airplay_status_contains_runtime_readiness():
    status = build_source().status().to_dict()
    assert status["details"]["runtime"]["ready"] is True
    assert status["details"]["runtime"]["binary_path"] == "/usr/bin/shairport-sync"

class MissingRuntimeInspector:
    def inspect(self, config):
        return AirPlayRuntimeReport(
            ready=False,
            binary_found=False,
            config_found=False,
            service_available=False,
            avahi_active=False,
            alsa_device_found=False,
            error="Nicht bereit: shairport-sync",
        )


def test_airplay_start_is_blocked_when_runtime_is_not_ready():
    source = AirPlaySource(
        controller=AirPlayController(),
        runtime_inspector=MissingRuntimeInspector(),
    )
    status = source.start()
    assert status.state is SourceLifecycleState.ERROR
    assert status.active is False
    assert "shairport-sync" in status.error
