from typing import Any

from tmba.core.event_bus import event_bus
from tmba.services.base_source_service import BaseSourceService


class AirPlayService(BaseSourceService):
    """
    Verwaltet AirPlay-Zustände und Metadaten.

    Die echte Steuerung über Shairport Sync wird später auf dem
    Raspberry Pi angebunden. Bis dahin kann der Dienst lokal simuliert
    und über die vorhandenen REST-Endpunkte getestet werden.
    """

    def __init__(self) -> None:
        super().__init__(
            source_name="airplay",
            default_title="AirPlay",
            default_artist="Warte auf Verbindung",
            default_album="TMBA-OS",
        )

        self._volume = 50

    def play(self) -> dict[str, Any]:
        """Setzt eine aktive AirPlay-Wiedergabe fort."""

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es besteht keine AirPlay-Verbindung.",
                "airplay": status,
            }

        self.set_playback_status("playing")

        return {
            "success": True,
            "airplay": self.get_status(),
        }

    def pause(self) -> dict[str, Any]:
        """Pausiert die aktive AirPlay-Wiedergabe."""

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es besteht keine AirPlay-Verbindung.",
                "airplay": status,
            }

        self.set_playback_status("paused")

        return {
            "success": True,
            "airplay": self.get_status(),
        }

    def stop(self) -> dict[str, Any]:
        """
        Stoppt die AirPlay-Wiedergabe.

        Die AirPlay-Sitzung bleibt bestehen.
        """

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es besteht keine AirPlay-Verbindung.",
                "airplay": status,
            }

        self.set_playback_status("stopped")

        return {
            "success": True,
            "airplay": self.get_status(),
        }

    def previous(self) -> dict[str, Any]:
        """
        Fordert den vorherigen Titel an.

        Die echte Fernsteuerung wird später über die AirPlay-Integration
        ergänzt.
        """

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es besteht keine AirPlay-Verbindung.",
                "airplay": status,
            }

        return {
            "success": True,
            "command": "previous",
            "airplay": status,
        }

    def next(self) -> dict[str, Any]:
        """
        Fordert den nächsten Titel an.

        Die echte Fernsteuerung wird später über die AirPlay-Integration
        ergänzt.
        """

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es besteht keine AirPlay-Verbindung.",
                "airplay": status,
            }

        return {
            "success": True,
            "command": "next",
            "airplay": status,
        }

    def set_volume(self, volume: int) -> dict[str, Any]:
        """
        Setzt die gespeicherte AirPlay-Lautstärke.

        Die Übergabe an Shairport Sync, PipeWire oder ALSA wird später
        ergänzt.
        """

        normalized_volume = self._normalize_volume(volume)
        self._volume = normalized_volume

        event_bus.publish(
            "player.volume_changed",
            {
                "source": "airplay",
                "volume": normalized_volume,
            },
        )

        return {
            "success": True,
            "volume": normalized_volume,
            "airplay": self.get_status(),
        }

    def get_volume(self) -> int:
        """Gibt die aktuell gespeicherte AirPlay-Lautstärke zurück."""

        return self._volume

    def connect_client(
        self,
        client_name: str = "",
    ) -> dict[str, Any]:
        """
        Simuliert den Start einer AirPlay-Sitzung.

        Diese Methode wird später durch Ereignisse von Shairport Sync
        aufgerufen.
        """

        normalized_client_name = client_name.strip() or "AirPlay-Gerät"

        self.session_started()

        self.update_metadata(
            title="AirPlay",
            artist=normalized_client_name,
            album="Verbunden",
            cover_url="",
            duration=0,
            elapsed=0,
        )

        self.set_playback_status("idle")

        return {
            "success": True,
            "client_name": normalized_client_name,
            "airplay": self.get_status(),
        }

    def disconnect_client(self) -> dict[str, Any]:
        """Beendet die AirPlay-Sitzung."""

        self.session_ended()

        return {
            "success": True,
            "airplay": self.get_status(),
        }

    def sync_state(
        self,
        *,
        connected: bool,
        client_name: str = "",
        playback_status: str = "idle",
        title: str = "",
        artist: str = "",
        album: str = "",
        cover_url: str = "",
        duration: int | float = 0,
        elapsed: int | float = 0,
        volume: int | None = None,
    ) -> dict[str, Any]:
        """
        Synchronisiert den AirPlay-Zustand aus einer externen Quelle.

        Diese Methode ist später der zentrale Einstiegspunkt für
        Shairport-Sync-Ereignisse.
        """

        if not connected:
            return self.disconnect_client()

        current_status = self.get_status()

        if not current_status.get("available", False):
            self.session_started()

        normalized_client_name = client_name.strip() or "AirPlay-Gerät"

        self.update_metadata(
            title=title.strip() or "AirPlay",
            artist=artist.strip() or normalized_client_name,
            album=album.strip() or "AirPlay-Audio",
            cover_url=cover_url,
            duration=duration,
            elapsed=elapsed,
        )

        self.set_playback_status(playback_status)

        if volume is not None:
            self.set_volume(volume)

        return {
            "success": True,
            "client_name": normalized_client_name,
            "airplay": self.get_status(),
        }

    @staticmethod
    def _normalize_volume(value: Any) -> int:
        try:
            numeric_value = int(float(value))
        except (TypeError, ValueError):
            numeric_value = 0

        return max(0, min(100, numeric_value))


airplay_service = AirPlayService()