"""Reusable AudioSource implementation for externally managed services."""

from __future__ import annotations

from abc import abstractmethod
from threading import RLock

from tmba.audio.sources.base import (
    AudioSource, SourceCapabilities, SourceLifecycleState, SourceStatus,
)
from tmba.audio.sources.service_process import (
    ServiceControlError, ServiceController, ServiceRuntimeState,
    ServiceSnapshot, SystemdServiceController,
)


class ServiceSource(AudioSource):
    """Base class for audio sources backed by a system service."""

    def __init__(
        self,
        service_name: str,
        *,
        controller: ServiceController | None = None,
        stop_service_on_disconnect: bool = True,
    ) -> None:
        self._service_name = service_name
        self._controller = controller or SystemdServiceController()
        self._stop_on_disconnect = stop_service_on_disconnect
        self._connected = False
        self._state = SourceLifecycleState.DISCONNECTED
        self._error: str | None = None
        self._snapshot: ServiceSnapshot | None = None
        self._lock = RLock()

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            can_pause=False,
            can_resume=False,
            provides_pcm=False,
            provides_metadata=True,
            externally_controlled=True,
        )

    def connect(self) -> SourceStatus:
        with self._lock:
            self._state = SourceLifecycleState.CONNECTING
            self._error = None
        try:
            snapshot = self._controller.inspect(self._service_name)
            if snapshot.state is ServiceRuntimeState.FAILED:
                raise ServiceControlError(
                    f"Dienst {snapshot.name} befindet sich im Fehlerzustand."
                )
        except Exception as error:
            return self._set_error(error)
        with self._lock:
            self._snapshot = snapshot
            self._connected = True
            self._state = SourceLifecycleState.READY
        return self.status()

    def disconnect(self) -> SourceStatus:
        try:
            if self._stop_on_disconnect and self._service_running():
                self._snapshot = self._controller.stop(self._service_name)
        except Exception as error:
            return self._set_error(error)
        with self._lock:
            self._connected = False
            self._state = SourceLifecycleState.DISCONNECTED
            self._error = None
        return self.status()

    def start(self) -> SourceStatus:
        if not self._connected:
            connected = self.connect()
            if connected.state is SourceLifecycleState.ERROR:
                return connected
        with self._lock:
            self._state = SourceLifecycleState.STARTING
            self._error = None
        try:
            snapshot = self._controller.start(self._service_name)
            if not snapshot.running:
                raise ServiceControlError(
                    f"Dienst {snapshot.name} wurde nicht aktiv."
                )
        except Exception as error:
            return self._set_error(error)
        with self._lock:
            self._snapshot = snapshot
            # The daemon is ready; actual playback is controlled externally.
            self._state = SourceLifecycleState.READY
        return self.status()

    def stop(self) -> SourceStatus:
        with self._lock:
            self._state = SourceLifecycleState.STOPPING
            self._error = None
        try:
            snapshot = self._controller.stop(self._service_name)
        except Exception as error:
            return self._set_error(error)
        with self._lock:
            self._snapshot = snapshot
            self._state = (
                SourceLifecycleState.READY
                if self._connected
                else SourceLifecycleState.DISCONNECTED
            )
        return self.status()

    def restart(self) -> SourceStatus:
        if not self._connected:
            connected = self.connect()
            if connected.state is SourceLifecycleState.ERROR:
                return connected
        with self._lock:
            self._state = SourceLifecycleState.STARTING
            self._error = None
        try:
            snapshot = self._controller.restart(self._service_name)
            if not snapshot.running:
                raise ServiceControlError(
                    f"Dienst {snapshot.name} wurde nach Neustart nicht aktiv."
                )
        except Exception as error:
            return self._set_error(error)
        with self._lock:
            self._snapshot = snapshot
            self._state = SourceLifecycleState.READY
        return self.status()

    def refresh(self) -> SourceStatus:
        if not self._connected:
            return self.status()
        try:
            snapshot = self._controller.inspect(self._service_name)
        except Exception as error:
            return self._set_error(error)
        with self._lock:
            self._snapshot = snapshot
            if snapshot.state is ServiceRuntimeState.FAILED:
                self._state = SourceLifecycleState.ERROR
                self._error = f"Dienst {snapshot.name} ist fehlgeschlagen."
            elif self._state is SourceLifecycleState.ERROR:
                self._state = SourceLifecycleState.READY
                self._error = None
        return self.status()

    def status(self) -> SourceStatus:
        with self._lock:
            snapshot = self._snapshot
            details = {
                "service_name": self._service_name,
                "service": snapshot.to_dict() if snapshot else None,
                "stop_service_on_disconnect": self._stop_on_disconnect,
            }
            return SourceStatus(
                source=self.source,
                state=self._state,
                connected=self._connected,
                active=bool(snapshot and snapshot.running),
                error=self._error,
                metadata={},
                details=details,
            )

    def _service_running(self) -> bool:
        with self._lock:
            return bool(self._snapshot and self._snapshot.running)

    def _set_error(self, error: Exception) -> SourceStatus:
        with self._lock:
            self._state = SourceLifecycleState.ERROR
            self._error = str(error)
        return self.status()
