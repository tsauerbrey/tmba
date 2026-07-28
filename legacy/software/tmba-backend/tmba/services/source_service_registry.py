from typing import Any

from tmba.services.airplay_service import airplay_service
from tmba.services.bluetooth_service import bluetooth_service
from tmba.services.webradio_service import webradio_service


class SourceServiceRegistry:
    """Verwaltet die verfügbaren quellenspezifischen Dienste."""

    def __init__(self) -> None:
        self._services = {
            "airplay": airplay_service,
            "bluetooth": bluetooth_service,
            "webradio": webradio_service,
        }

    def get_service(self, source: str) -> Any | None:
        normalized_source = source.strip().lower()
        return self._services.get(normalized_source)

    def get_status(self, source: str) -> dict[str, Any] | None:
        service = self.get_service(source)

        if service is None:
            return None

        return service.get_status()


source_service_registry = SourceServiceRegistry()