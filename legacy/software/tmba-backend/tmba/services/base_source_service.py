from threading import Lock
from typing import Any

from tmba.core.event_bus import event_bus


class BaseSourceService:
    """Gemeinsame Basis für Audioquellen des TMBA-Players."""

    VALID_PLAYBACK_STATUSES = {
        "idle",
        "playing",
        "paused",
        "stopped",
    }

    STATUS_ALIASES = {
        "play": "playing",
        "pause": "paused",
        "stop": "stopped",
    }

    def __init__(
        self,
        *,
        source_name: str,
        default_title: str,
        default_artist: str,
        default_album: str = "TMBA-OS",
    ) -> None:
        self._lock = Lock()

        self._source_name = source_name.strip().lower()
        self._default_title = default_title
        self._default_artist = default_artist
        self._default_album = default_album

        self._available = False
        self._status = "idle"
        self._track = self._create_default_track()

    def session_started(self) -> dict[str, Any]:
        """Markiert den Beginn einer Quellensitzung."""

        with self._lock:
            self._available = True
            self._status = "playing"

        event_bus.publish(
            "source.availability_changed",
            {
                "source": self._source_name,
                "available": True,
            },
        )

        event_bus.publish(
            "player.status_changed",
            {
                "source": self._source_name,
                "status": "playing",
            },
        )

        return self.get_status()

    def session_ended(self) -> dict[str, Any]:
        """Markiert das Ende einer Quellensitzung."""

        with self._lock:
            self._available = False
            self._status = "idle"
            self._track = self._create_default_track()

        event_bus.publish(
            "source.availability_changed",
            {
                "source": self._source_name,
                "available": False,
            },
        )

        return self.get_status()

    def update_metadata(
        self,
        *,
        title: str = "",
        artist: str = "",
        album: str = "",
        cover_url: str = "",
        duration: int | float = 0,
        elapsed: int | float = 0,
    ) -> dict[str, Any]:
        """Aktualisiert die Metadaten der Quelle."""

        track = {
            "title": title or "Unbekannter Titel",
            "artist": artist or "Unbekannter Interpret",
            "album": album,
            "cover_url": cover_url,
            "duration": self._normalize_time(duration),
            "elapsed": self._normalize_time(elapsed),
        }

        with self._lock:
            self._track = track

        self._publish_track_changed(track)

        return self.get_status()

    def update_progress(
        self,
        *,
        elapsed: int | float,
        duration: int | float | None = None,
    ) -> dict[str, Any]:
        """Aktualisiert Abspielposition und optional die Gesamtdauer."""

        normalized_elapsed = self._normalize_time(elapsed)

        with self._lock:
            self._track["elapsed"] = normalized_elapsed

            if duration is not None:
                self._track["duration"] = self._normalize_time(
                    duration
                )

            track = self._track.copy()

        self._publish_track_changed(track)

        return self.get_status()

    def set_playback_status(
        self,
        status: str,
    ) -> dict[str, Any]:
        """Aktualisiert den Wiedergabestatus der Quelle."""

        normalized_status = status.strip().lower()
        normalized_status = self.STATUS_ALIASES.get(
            normalized_status,
            normalized_status,
        )

        if normalized_status not in self.VALID_PLAYBACK_STATUSES:
            raise ValueError(
                f"Ungültiger Wiedergabestatus für "
                f"{self._source_name}: {normalized_status}"
            )

        with self._lock:
            self._status = normalized_status

        event_bus.publish(
            "player.status_changed",
            {
                "source": self._source_name,
                "status": normalized_status,
            },
        )

        return self.get_status()

    def get_status(self) -> dict[str, Any]:
        """Gibt eine Kopie des aktuellen Quellenzustands zurück."""

        with self._lock:
            return {
                "source": self._source_name,
                "available": self._available,
                "status": self._status,
                "track": self._track.copy(),
            }

    def _publish_track_changed(
        self,
        track: dict[str, Any],
    ) -> None:
        event_bus.publish(
            "player.track_changed",
            {
                "source": self._source_name,
                "track": track.copy(),
            },
        )

    def _create_default_track(self) -> dict[str, Any]:
        return {
            "title": self._default_title,
            "artist": self._default_artist,
            "album": self._default_album,
            "cover_url": "",
            "duration": 0,
            "elapsed": 0,
        }

    @staticmethod
    def _normalize_time(value: Any) -> int:
        try:
            numeric_value = int(float(value))
        except (TypeError, ValueError):
            numeric_value = 0

        return max(0, numeric_value)