from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any

from tmba.core.event_bus import event_bus


@dataclass(frozen=True)
class SourceInfo:
    """Beschreibung einer Audioquelle."""

    name: str
    display_name: str
    priority: int
    default_title: str
    default_artist: str
    default_album: str = "TMBA-OS"


class SourceManager:
    """Verwaltet verfügbare und aktive Audioquellen."""

    def __init__(self) -> None:
        self._lock = Lock()

        self._sources: dict[str, SourceInfo] = {
            "none": SourceInfo(
                name="none",
                display_name="Keine Quelle",
                priority=0,
                default_title="Keine Wiedergabe",
                default_artist="Quelle auswählen",
            ),
            "webradio": SourceInfo(
                name="webradio",
                display_name="Webradio",
                priority=10,
                default_title="Webradio",
                default_artist="Sender auswählen",
            ),
            "usb": SourceInfo(
                name="usb",
                display_name="USB/NAS",
                priority=20,
                default_title="USB/NAS",
                default_artist="Musik auswählen",
            ),
            "bluetooth": SourceInfo(
                name="bluetooth",
                display_name="Bluetooth",
                priority=30,
                default_title="Bluetooth",
                default_artist="Gerät verbinden",
            ),
            "airplay": SourceInfo(
                name="airplay",
                display_name="AirPlay",
                priority=40,
                default_title="AirPlay",
                default_artist="Warte auf Verbindung",
            ),
        }

        self._active_source = "none"

        self._source_available: dict[str, bool] = {
            source_name: source_name == "none"
            for source_name in self._sources
        }

        event_bus.subscribe(
            "source.availability_changed",
            self._handle_source_availability_changed,
        )

    def _handle_source_availability_changed(
        self,
        data: dict[str, Any],
    ) -> None:
        """Verarbeitet eine Verfügbarkeitsmeldung vom EventBus."""

        source = data.get("source")
        available = data.get("available")

        if not isinstance(source, str):
            raise ValueError(
                "Das Ereignis benötigt einen gültigen Quellennamen."
            )

        if not isinstance(available, bool):
            raise ValueError(
                "Das Ereignis benötigt 'available' als Wahrheitswert."
            )

        previous_source = self.get_active_source()

        active_source = self.set_source_available(
            source,
            available,
        )

        if active_source != previous_source:
            event_bus.publish(
                "source.changed",
                {
                    "source": active_source,
                    "previous_source": previous_source,
                },
            )

    def normalize_source(self, source: str) -> str:
        """Vereinheitlicht und prüft einen Quellennamen."""

        normalized_source = source.strip().lower()

        if normalized_source not in self._sources:
            raise ValueError(
                f"Unbekannte Audioquelle: {normalized_source}"
            )

        return normalized_source

    def select_source(self, source: str) -> str:
        """Aktiviert eine Audioquelle und gibt ihren Namen zurück."""

        normalized_source = self.normalize_source(source)

        with self._lock:
            self._active_source = normalized_source

        return normalized_source

    def get_active_source(self) -> str:
        """Gibt den Namen der aktiven Audioquelle zurück."""

        with self._lock:
            return self._active_source

    def set_source_available(
        self,
        source: str,
        available: bool,
    ) -> str:
        """Setzt den Verfügbarkeitszustand einer Quelle."""

        normalized_source = self.normalize_source(source)

        if normalized_source == "none":
            available = True

        with self._lock:
            self._source_available[normalized_source] = bool(available)

        return self.select_highest_priority_source()

    def is_source_available(self, source: str) -> bool:
        """Prüft, ob eine Quelle aktuell verfügbar ist."""

        normalized_source = self.normalize_source(source)

        with self._lock:
            return self._source_available.get(
                normalized_source,
                False,
            )

    def select_highest_priority_source(self) -> str:
        """Wählt die verfügbare Quelle mit der höchsten Priorität."""

        with self._lock:
            available_sources = [
                source
                for source in self._sources.values()
                if self._source_available.get(source.name, False)
            ]

            if not available_sources:
                self._active_source = "none"
                return self._active_source

            highest_priority_source = max(
                available_sources,
                key=lambda source: source.priority,
            )

            self._active_source = highest_priority_source.name
            return self._active_source

    def get_source_info(
        self,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Liefert Informationen zu einer Audioquelle."""

        if source is None:
            source = self.get_active_source()

        normalized_source = self.normalize_source(source)
        source_info = asdict(self._sources[normalized_source])
        source_info["available"] = self.is_source_available(
            normalized_source
        )

        return source_info

    def list_sources(self) -> list[dict[str, Any]]:
        """Liefert alle verfügbaren Audioquellen."""

        with self._lock:
            sources = sorted(
                self._sources.values(),
                key=lambda item: item.priority,
                reverse=True,
            )

            availability = self._source_available.copy()

        return [
            {
                **asdict(source),
                "available": availability.get(source.name, False),
            }
            for source in sources
        ]

    def default_track_for_source(
        self,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Erzeugt die Standardanzeige einer Audioquelle."""

        source_info = self.get_source_info(source)

        return {
            "title": source_info["default_title"],
            "artist": source_info["default_artist"],
            "album": source_info["default_album"],
            "cover_url": "",
            "duration": 0,
            "elapsed": 0,
        }


source_manager = SourceManager()