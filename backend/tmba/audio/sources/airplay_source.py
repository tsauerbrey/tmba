"""AirPlay adapter for the shairport-sync system service."""

from __future__ import annotations

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources.service_process import ServiceController
from tmba.audio.sources.service_source import ServiceSource


class AirPlaySource(ServiceSource):
    """Represent shairport-sync through the common AudioSource API."""

    def __init__(
        self,
        *,
        controller: ServiceController | None = None,
        service_name: str = "shairport-sync.service",
        stop_service_on_disconnect: bool = True,
    ) -> None:
        super().__init__(
            service_name,
            controller=controller,
            stop_service_on_disconnect=stop_service_on_disconnect,
        )

    @property
    def source(self) -> EngineSource:
        return EngineSource.AIRPLAY

    @property
    def name(self) -> str:
        return "AirPlay"
