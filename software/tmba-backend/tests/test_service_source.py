from __future__ import annotations

from dataclasses import replace

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources.base import SourceLifecycleState
from tmba.audio.sources.service_process import (
    ServiceControlError, ServiceRuntimeState, ServiceSnapshot,
)
from tmba.audio.sources.service_source import ServiceSource


class FakeController:
    def __init__(self):
        self.snapshot = ServiceSnapshot("demo.service", ServiceRuntimeState.INACTIVE)
        self.calls = []
        self.error = None
    def _result(self, action):
        self.calls.append(action)
        if self.error: raise self.error
        return self.snapshot
    def inspect(self, name): return self._result("inspect")
    def start(self, name):
        self.snapshot = replace(self.snapshot, state=ServiceRuntimeState.ACTIVE, sub_state="running", main_pid=10)
        return self._result("start")
    def stop(self, name):
        self.snapshot = replace(self.snapshot, state=ServiceRuntimeState.INACTIVE, sub_state="dead", main_pid=None)
        return self._result("stop")
    def restart(self, name):
        self.snapshot = replace(self.snapshot, state=ServiceRuntimeState.ACTIVE, sub_state="running", main_pid=11)
        return self._result("restart")


class DemoSource(ServiceSource):
    @property
    def source(self): return EngineSource.WEBRADIO


def test_connect_inspects_service_without_starting_it():
    controller = FakeController()
    source = DemoSource("demo.service", controller=controller)
    status = source.connect()
    assert status.state is SourceLifecycleState.READY
    assert status.connected is True
    assert status.active is False
    assert controller.calls == ["inspect"]


def test_start_connects_and_starts_service():
    controller = FakeController()
    status = DemoSource("demo.service", controller=controller).start()
    assert status.state is SourceLifecycleState.READY
    assert status.active is True
    assert controller.calls == ["inspect", "start"]


def test_disconnect_stops_owned_running_service():
    controller = FakeController()
    source = DemoSource("demo.service", controller=controller)
    source.start()
    status = source.disconnect()
    assert status.state is SourceLifecycleState.DISCONNECTED
    assert status.connected is False
    assert controller.calls[-1] == "stop"


def test_refresh_turns_failed_service_into_source_error():
    controller = FakeController()
    source = DemoSource("demo.service", controller=controller)
    source.connect()
    controller.snapshot = replace(controller.snapshot, state=ServiceRuntimeState.FAILED)
    status = source.refresh()
    assert status.state is SourceLifecycleState.ERROR
    assert "fehlgeschlagen" in status.error


def test_controller_error_is_normalized_into_status():
    controller = FakeController()
    controller.error = ServiceControlError("boom")
    status = DemoSource("demo.service", controller=controller).connect()
    assert status.state is SourceLifecycleState.ERROR
    assert status.error == "boom"


def test_restart_exposes_active_snapshot():
    controller = FakeController()
    source = DemoSource("demo.service", controller=controller)
    status = source.restart()
    assert status.active is True
    assert status.details["service"]["main_pid"] == 11
