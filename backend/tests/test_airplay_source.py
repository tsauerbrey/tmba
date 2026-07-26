from __future__ import annotations

from tmba.audio.engine_state import EngineSource
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


def test_airplay_adapter_has_stable_identity_and_capabilities():
    source = AirPlaySource(controller=AirPlayController())
    assert source.source is EngineSource.AIRPLAY
    assert source.name == "AirPlay"
    assert source.service_name == "shairport-sync.service"
    assert source.capabilities.externally_controlled is True
    assert source.capabilities.can_pause is False


def test_airplay_adapter_starts_and_stops_shairport_service():
    source = AirPlaySource(controller=AirPlayController())
    started = source.start()
    assert started.state is SourceLifecycleState.READY
    assert started.active is True
    stopped = source.stop()
    assert stopped.active is False
    assert stopped.connected is True
