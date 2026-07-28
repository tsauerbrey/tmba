from typing import Any

from tmba.core.event_bus import event_bus
from tmba.services.base_source_service import BaseSourceService


class BluetoothService(BaseSourceService):
    """
    Verwaltet Bluetooth-Audiozustände und Metadaten.

    Die eigentliche Steuerung über BlueZ und PipeWire wird später ergänzt.
    Bis dahin stellt der Dienst eine einheitliche Schnittstelle für
    PlayerService, REST-API und GUI bereit.
    """

    def __init__(self) -> None:
        super().__init__(
            source_name="bluetooth",
            default_title="Bluetooth",
            default_artist="Gerät verbinden",
            default_album="TMBA-OS",
        )

        self._volume = 50

    def play(self) -> dict[str, Any]:
        """Setzt eine aktive Bluetooth-Wiedergabe fort."""

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es ist kein Bluetooth-Gerät verbunden.",
                "bluetooth": status,
            }

        self.set_playback_status("playing")

        return {
            "success": True,
            "bluetooth": self.get_status(),
        }

    def pause(self) -> dict[str, Any]:
        """Pausiert die aktive Bluetooth-Wiedergabe."""

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es ist kein Bluetooth-Gerät verbunden.",
                "bluetooth": status,
            }

        self.set_playback_status("paused")

        return {
            "success": True,
            "bluetooth": self.get_status(),
        }

    def stop(self) -> dict[str, Any]:
        """
        Stoppt die Bluetooth-Wiedergabe.

        Die Verbindung bleibt bestehen. Nur der Wiedergabestatus wird
        auf stopped gesetzt.
        """

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es ist kein Bluetooth-Gerät verbunden.",
                "bluetooth": status,
            }

        self.set_playback_status("stopped")

        return {
            "success": True,
            "bluetooth": self.get_status(),
        }

    def previous(self) -> dict[str, Any]:
        """
        Fordert den vorherigen Bluetooth-Titel an.

        Die echte AVRCP-Steuerung wird später über BlueZ ergänzt.
        """

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es ist kein Bluetooth-Gerät verbunden.",
                "bluetooth": status,
            }

        return {
            "success": True,
            "command": "previous",
            "bluetooth": status,
        }

    def next(self) -> dict[str, Any]:
        """
        Fordert den nächsten Bluetooth-Titel an.

        Die echte AVRCP-Steuerung wird später über BlueZ ergänzt.
        """

        status = self.get_status()

        if not status.get("available", False):
            return {
                "success": False,
                "error": "Es ist kein Bluetooth-Gerät verbunden.",
                "bluetooth": status,
            }

        return {
            "success": True,
            "command": "next",
            "bluetooth": status,
        }

    def set_volume(self, volume: int) -> dict[str, Any]:
        """
        Setzt die zentrale Bluetooth-Lautstärke.

        Die Hardware-Ausgabe über PipeWire oder ALSA wird später ergänzt.
        """

        normalized_volume = self._normalize_volume(volume)
        self._volume = normalized_volume

        event_bus.publish(
            "player.volume_changed",
            {
                "source": "bluetooth",
                "volume": normalized_volume,
            },
        )

        return {
            "success": True,
            "volume": normalized_volume,
            "bluetooth": self.get_status(),
        }

    def get_volume(self) -> int:
        """Gibt die aktuell gespeicherte Bluetooth-Lautstärke zurück."""

        return self._volume

    def connect_device(
        self,
        device_name: str = "",
    ) -> dict[str, Any]:
        """
        Simuliert das Verbinden eines Bluetooth-Geräts.

        Diese Methode wird später durch echte BlueZ-Ereignisse aufgerufen.
        """

        normalized_device_name = (
            device_name.strip() or "Bluetooth-Gerät"
        )

        self.session_started()

        self.update_metadata(
            title="Bluetooth",
            artist=normalized_device_name,
            album="Verbunden",
            cover_url="",
            duration=0,
            elapsed=0,
        )

        self.set_playback_status("idle")

        return {
            "success": True,
            "device_name": normalized_device_name,
            "bluetooth": self.get_status(),
        }

    def disconnect_device(self) -> dict[str, Any]:
        """
        Simuliert das Trennen des Bluetooth-Geräts.
        """

        self.session_ended()

        return {
            "success": True,
            "bluetooth": self.get_status(),
        }

    def sync_state(
        self,
        *,
        connected: bool,
        device_name: str = "",
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
        Synchronisiert den Bluetooth-Zustand aus einer externen Quelle.

        Diese Methode ist später der zentrale Einstiegspunkt für BlueZ- und
        PipeWire-Ereignisse.
        """

        if not connected:
            return self.disconnect_device()

        current_status = self.get_status()

        if not current_status.get("available", False):
            self.session_started()

        normalized_device_name = (
            device_name.strip() or "Bluetooth-Gerät"
        )

        self.update_metadata(
            title=title.strip() or "Bluetooth",
            artist=artist.strip() or normalized_device_name,
            album=album.strip() or "Bluetooth-Audio",
            cover_url=cover_url,
            duration=duration,
            elapsed=elapsed,
        )

        self.set_playback_status(playback_status)

        if volume is not None:
            self.set_volume(volume)

        return {
            "success": True,
            "device_name": normalized_device_name,
            "bluetooth": self.get_status(),
        }

    @staticmethod
    def _normalize_volume(value: Any) -> int:
        try:
            numeric_value = int(float(value))
        except (TypeError, ValueError):
            numeric_value = 0

        return max(0, min(100, numeric_value))


bluetooth_service = BluetoothService()