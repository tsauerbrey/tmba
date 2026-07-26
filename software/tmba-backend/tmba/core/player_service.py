from threading import Lock
from typing import Any

from tmba.core.event_bus import event_bus
from tmba.core.source_manager import source_manager
from tmba.services.source_service_registry import (
    source_service_registry,
)


class PlayerService:
    """
    Zentraler Zustand und Befehlsverteiler des TMBA-Players.

    Der PlayerService greift nicht direkt auf MPD, AirPlay oder Bluetooth zu.
    Wiedergabebefehle werden an den Dienst der aktiven Quelle weitergeleitet.
    """

    def __init__(self) -> None:
        self._lock = Lock()

        self._status = "idle"
        self._volume = 50
        self._track = source_manager.default_track_for_source()

        event_bus.subscribe(
            "source.changed",
            self._handle_source_changed,
        )

        event_bus.subscribe(
            "player.status_changed",
            self._handle_player_status_changed,
        )

        event_bus.subscribe(
            "player.track_changed",
            self._handle_player_track_changed,
        )

        event_bus.subscribe(
            "player.volume_changed",
            self._handle_player_volume_changed,
        )

    def _handle_source_changed(
        self,
        data: dict[str, Any],
    ) -> None:
        """Synchronisiert den Player nach einem Quellenwechsel."""

        self.sync_active_source()

    def _handle_player_status_changed(
        self,
        data: dict[str, Any],
    ) -> None:
        """Übernimmt den Wiedergabestatus der aktiven Quelle."""

        source = data.get("source")
        status = data.get("status")

        if not isinstance(source, str):
            raise ValueError(
                "Das Statusereignis benötigt einen Quellennamen."
            )

        if not isinstance(status, str):
            raise ValueError(
                "Das Statusereignis benötigt einen Wiedergabestatus."
            )

        normalized_source = source_manager.normalize_source(source)
        active_source = source_manager.get_active_source()

        if normalized_source != active_source:
            return

        normalized_status = self._normalize_status(status)

        with self._lock:
            self._status = normalized_status

    def _handle_player_track_changed(
        self,
        data: dict[str, Any],
    ) -> None:
        """Übernimmt Titelinformationen der aktiven Quelle."""

        source = data.get("source")
        track = data.get("track")

        if not isinstance(source, str):
            raise ValueError(
                "Das Titelereignis benötigt einen Quellennamen."
            )

        if not isinstance(track, dict):
            raise ValueError(
                "Das Titelereignis benötigt gültige Titeldaten."
            )

        normalized_source = source_manager.normalize_source(source)
        active_source = source_manager.get_active_source()

        if normalized_source != active_source:
            return

        normalized_track = self._normalize_track(track)

        with self._lock:
            self._track = normalized_track

    def _handle_player_volume_changed(
        self,
        data: dict[str, Any],
    ) -> None:
        """Übernimmt eine Lautstärkeänderung vom EventBus."""

        volume = data.get("volume")

        if volume is None:
            return

        with self._lock:
            self._volume = self._normalize_volume(volume)

    def get_status(self) -> dict[str, Any]:
        """Gibt eine vollständige Kopie des Player-Zustands zurück."""

        active_source = source_manager.get_active_source()

        with self._lock:
            return {
                "status": self._status,
                "source": active_source,
                "volume": self._volume,
                "track": self._track.copy(),
            }

    def set_volume(self, volume: int) -> dict[str, Any]:
        """
        Setzt die Lautstärke.

        Unterstützt der aktive Quellendienst set_volume(), wird der Befehl
        dorthin weitergeleitet. Andernfalls wird zunächst nur der zentrale
        Player-Zustand aktualisiert.
        """

        normalized_volume = self._normalize_volume(volume)
        service = self._get_active_source_service()

        if service is not None:
            command = getattr(service, "set_volume", None)

            if callable(command):
                result = command(normalized_volume)

                if isinstance(result, dict):
                    normalized_volume = self._extract_volume(
                        result,
                        normalized_volume,
                    )

        with self._lock:
            self._volume = normalized_volume

        event_bus.publish(
            "player.volume_changed",
            {
                "source": source_manager.get_active_source(),
                "volume": normalized_volume,
            },
        )

        return self.get_status()

    def select_source(self, source: str) -> dict[str, Any]:
        """
        Wählt eine Quelle aus.

        Die tatsächliche automatische Quellenwahl wird weiterhin vom
        SourceManager anhand der Verfügbarkeit vorgenommen.
        """

        normalized_source = source_manager.select_source(source)

        with self._lock:
            self._status = "idle"
            self._track = source_manager.default_track_for_source(
                normalized_source
            )

        self.sync_active_source()
        return self.get_status()

    def sync_active_source(self) -> dict[str, Any]:
        """Übernimmt den gespeicherten Zustand der aktiven Quelle."""

        active_source = source_manager.get_active_source()
        source_status = source_service_registry.get_status(
            active_source
        )

        if source_status is None:
            with self._lock:
                self._status = "idle"
                self._track = (
                    source_manager.default_track_for_source(
                        active_source
                    )
                )

            return self.get_status()

        status = self._normalize_status(
            source_status.get("status", "idle")
        )

        track = source_status.get("track")

        if not isinstance(track, dict):
            track = source_manager.default_track_for_source(
                active_source
            )

        with self._lock:
            self._status = status
            self._track = self._normalize_track(track)

        return self.get_status()

    def play(self) -> dict[str, Any]:
        """Leitet Play an den aktiven Quellendienst weiter."""

        return self._execute_source_command("play")

    def pause(self) -> dict[str, Any]:
        """Leitet Pause an den aktiven Quellendienst weiter."""

        return self._execute_source_command("pause")

    def stop(self) -> dict[str, Any]:
        """Leitet Stop an den aktiven Quellendienst weiter."""

        return self._execute_source_command("stop")

    def previous(self) -> dict[str, Any]:
        """Leitet Zurück an den aktiven Quellendienst weiter."""

        return self._execute_source_command("previous")

    def next(self) -> dict[str, Any]:
        """Leitet Weiter an den aktiven Quellendienst weiter."""

        return self._execute_source_command("next")

    def update_track(
        self,
        *,
        title: str,
        artist: str = "",
        album: str = "",
        cover_url: str = "",
        duration: int | float = 0,
        elapsed: int | float = 0,
    ) -> dict[str, Any]:
        """
        Aktualisiert den zentralen Titelzustand.

        Diese Methode bleibt vorerst für bestehende API-Kompatibilität
        erhalten. Neue Quellendienste sollten Titeländerungen über den
        EventBus veröffentlichen.
        """

        track = self._normalize_track(
            {
                "title": title,
                "artist": artist,
                "album": album,
                "cover_url": cover_url,
                "duration": duration,
                "elapsed": elapsed,
            }
        )

        with self._lock:
            self._track = track

        return self.get_status()

    def _execute_source_command(
        self,
        command_name: str,
    ) -> dict[str, Any]:
        """Führt einen Befehl beim aktiven Quellendienst aus."""

        service = self._get_active_source_service()

        if service is None:
            return self.get_status()

        command = getattr(service, command_name, None)

        if not callable(command):
            return self.get_status()

        command()

        # Die SourceServices veröffentlichen ihre Änderungen synchron
        # über den EventBus. Danach gleichen wir vorsichtshalber noch
        # einmal mit dem gespeicherten Zustand der aktiven Quelle ab.
        self.sync_active_source()

        return self.get_status()

    @staticmethod
    def _get_active_source_service() -> Any | None:
        active_source = source_manager.get_active_source()

        return source_service_registry.get_service(
            active_source
        )

    def _normalize_track(
        self,
        track: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "title": str(
                track.get("title") or "Unbekannter Titel"
            ),
            "artist": str(
                track.get("artist") or "Unbekannter Interpret"
            ),
            "album": str(track.get("album") or ""),
            "cover_url": str(track.get("cover_url") or ""),
            "duration": self._normalize_time(
                track.get("duration", 0)
            ),
            "elapsed": self._normalize_time(
                track.get("elapsed", 0)
            ),
        }

    @staticmethod
    def _normalize_status(value: Any) -> str:
        normalized_status = str(
            value or "idle"
        ).strip().lower()

        status_mapping = {
            "play": "playing",
            "pause": "paused",
            "stop": "stopped",
        }

        normalized_status = status_mapping.get(
            normalized_status,
            normalized_status,
        )

        valid_statuses = {
            "idle",
            "playing",
            "paused",
            "stopped",
        }

        if normalized_status not in valid_statuses:
            return "idle"

        return normalized_status

    @staticmethod
    def _extract_volume(
        result: dict[str, Any],
        fallback: int,
    ) -> int:
        """
        Sucht eine Lautstärke sowohl auf oberster Ebene als auch
        im eingebetteten MPD-Ergebnis.
        """

        if "volume" in result:
            return PlayerService._normalize_volume(
                result["volume"]
            )

        mpd_result = result.get("mpd")

        if isinstance(mpd_result, dict):
            if "volume" in mpd_result:
                return PlayerService._normalize_volume(
                    mpd_result["volume"]
                )

        return fallback

    @staticmethod
    def _normalize_volume(value: Any) -> int:
        try:
            numeric_value = int(float(value))
        except (TypeError, ValueError):
            numeric_value = 0

        return max(0, min(100, numeric_value))

    @staticmethod
    def _normalize_time(value: Any) -> int:
        try:
            numeric_value = int(float(value))
        except (TypeError, ValueError):
            numeric_value = 0

        return max(0, numeric_value)


player_service = PlayerService()
