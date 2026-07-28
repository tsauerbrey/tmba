"""AirPlay adapter for the shairport-sync system service."""

from __future__ import annotations

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources.airplay_runtime import (
    AirPlayRuntimeConfig,
    AirPlayRuntimeInspector,
    AirPlayRuntimeReport,
)
from tmba.audio.sources.service_process import ServiceController
from tmba.audio.sources.service_source import ServiceSource


class AirPlaySource(ServiceSource):
    """Represent shairport-sync through the common AudioSource API."""

    def __init__(
        self,
        *,
        controller: ServiceController | None = None,
        runtime_config: AirPlayRuntimeConfig | None = None,
        runtime_inspector: AirPlayRuntimeInspector | None = None,
        service_name: str = "shairport-sync.service",
        stop_service_on_disconnect: bool = True,
    ) -> None:
        self._runtime_config = runtime_config or AirPlayRuntimeConfig(
            service_name=service_name
        )
        self._runtime_inspector = runtime_inspector or AirPlayRuntimeInspector()
        super().__init__(
            self._runtime_config.service_name,
            controller=controller,
            stop_service_on_disconnect=stop_service_on_disconnect,
        )

    @property
    def source(self) -> EngineSource:
        return EngineSource.AIRPLAY

    @property
    def name(self) -> str:
        return "AirPlay"

    @property
    def runtime_config(self) -> AirPlayRuntimeConfig:
        return self._runtime_config

    def inspect_runtime(self) -> AirPlayRuntimeReport:
        """Return host readiness without starting or stopping services."""

        return self._runtime_inspector.inspect(self._runtime_config)


    def start(self):
        runtime = self.inspect_runtime()
        if not runtime.ready:
            return self._set_error(
                RuntimeError(runtime.error or "AirPlay-Laufzeit ist nicht bereit.")
            )
        return super().start()

    def status(self):
        status = super().status()
        runtime = self.inspect_runtime()
        details = dict(status.details or {})
        details["runtime"] = runtime.to_dict()
        return type(status)(
            source=status.source,
            state=status.state,
            connected=status.connected,
            active=status.active,
            error=status.error,
            metadata=status.metadata,
            details=details,
        )
