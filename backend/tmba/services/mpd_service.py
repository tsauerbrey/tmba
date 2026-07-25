from threading import Lock
from typing import Any

from mpd import (
    CommandError,
    ConnectionError as MPDConnectionError,
    MPDClient,
    ProtocolError,
)


class MPDService:
    """Schnittstelle zwischen TMBA-OS und Music Player Daemon."""
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6600,
        timeout: int = 3,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

        self._client: MPDClient | None = None
        self._lock = Lock()

    def _create_client(self) -> MPDClient:
        client = MPDClient()
        client.timeout = self.timeout
        client.idletimeout = None
        return client

    def connect(self) -> bool:
        """Baut eine Verbindung zum MPD-Server auf."""

        with self._lock:
            if self._client is not None:
                try:
                    self._client.ping()
                    return True
                except (CommandError, MPDConnectionError, ProtocolError, OSError):
                    self._disconnect_unlocked()

            client = self._create_client()

            try:
                client.connect(self.host, self.port)
                self._client = client
                return True
            except (CommandError, MPDConnectionError, ProtocolError, OSError):
                try:
                    client.disconnect()
                except (CommandError, MPDConnectionError, ProtocolError, OSError):
                    pass

                self._client = None
                return False

    def disconnect(self) -> None:
        """Trennt die Verbindung zum MPD-Server."""

        with self._lock:
            self._disconnect_unlocked()

    def _disconnect_unlocked(self) -> None:
        if self._client is None:
            return

        try:
            self._client.close()
        except (CommandError, MPDConnectionError, ProtocolError, OSError):
            pass

        try:
            self._client.disconnect()
        except (CommandError, MPDConnectionError, ProtocolError, OSError):
            pass

        self._client = None

    def _ensure_connection(self) -> MPDClient | None:
        if not self.connect():
            return None

        return self._client

    def get_status(self) -> dict[str, Any]:
        """Liefert den aktuellen MPD-Wiedergabestatus."""

        client = self._ensure_connection()

        if client is None:
            return self._offline_status()

        with self._lock:
            try:
                status = client.status()
            except (CommandError, MPDConnectionError, ProtocolError, OSError):
                self._disconnect_unlocked()
                return self._offline_status()

        return {
            "connected": True,
            "state": status.get("state", "stop"),
            "volume": self._to_int(status.get("volume"), 0),
            "elapsed": self._to_float(status.get("elapsed"), 0),
            "duration": self._to_float(status.get("duration"), 0),
        }

    def get_current_track(self) -> dict[str, Any]:
        """Liefert Metadaten des aktuell geladenen Titels."""

        client = self._ensure_connection()

        if client is None:
            return self._empty_track()

        with self._lock:
            try:
                song = client.currentsong()
                status = client.status()
            except (CommandError, MPDConnectionError, ProtocolError, OSError):
                self._disconnect_unlocked()
                return self._empty_track()

        return {
            "title": song.get("title", ""),
            "artist": song.get("artist", ""),
            "album": song.get("album", ""),
            "file": song.get("file", ""),
            "cover_url": "",
            "duration": self._to_float(
                status.get("duration", song.get("duration")),
                0,
            ),
            "elapsed": self._to_float(status.get("elapsed"), 0),
        }


    def load_stream(
        self,
        url: str,
        station_name: str = "",
    ) -> dict[str, Any]:
        """Lädt eine Stream-URL in MPD und startet die Wiedergabe."""

        normalized_url = url.strip()
        normalized_station_name = station_name.strip()

        if not normalized_url:
            return {
                "success": False,
                "connected": False,
                "state": "stop",
                "url": "",
                "station_name": normalized_station_name,
                "error": "Es wurde keine Stream-URL angegeben.",
            }

        client = self._ensure_connection()

        if client is None:
            return {
                "success": False,
                "connected": False,
                "state": "stop",
                "url": normalized_url,
                "station_name": normalized_station_name,
                "error": "MPD ist nicht erreichbar.",
            }

        with self._lock:
            try:
                client.stop()
                client.clear()
                client.add(normalized_url)
                client.play()

                status = client.status()
            except (
                CommandError,
                MPDConnectionError,
                ProtocolError,
                OSError,
            ) as error:
                self._disconnect_unlocked()

                return {
                    "success": False,
                    "connected": False,
                    "state": "stop",
                    "url": normalized_url,
                    "station_name": normalized_station_name,
                    "error": str(error),
                }

        return {
            "success": True,
            "connected": True,
            "state": status.get("state", "play"),
            "url": normalized_url,
            "station_name": normalized_station_name,
        }


    def play(self) -> dict[str, Any]:
        return self._execute_playback_command("play")

    def pause(self) -> dict[str, Any]:
        return self._execute_playback_command("pause", 1)

    def stop(self) -> dict[str, Any]:
        return self._execute_playback_command("stop")
    
    def previous(self) -> dict[str, Any]:
        """Wechselt zum vorherigen Titel in der MPD-Wiedergabeliste."""

        return self._execute_playback_command("previous")

    def next(self) -> dict[str, Any]:
        """Wechselt zum nächsten Titel in der MPD-Wiedergabeliste."""

        return self._execute_playback_command("next")

    def set_volume(self, volume: int) -> dict[str, Any]:
        normalized_volume = max(0, min(100, int(volume)))
        client = self._ensure_connection()

        if client is None:
            return {
                "success": False,
                "connected": False,
                "volume": normalized_volume,
                "error": "MPD ist nicht erreichbar.",
            }

        with self._lock:
            try:
                client.setvol(normalized_volume)
            except (CommandError, MPDConnectionError, ProtocolError, OSError) as error:
                self._disconnect_unlocked()

                return {
                    "success": False,
                    "connected": False,
                    "volume": normalized_volume,
                    "error": str(error),
                }

        return {
            "success": True,
            "connected": True,
            "volume": normalized_volume,
        }

    def _execute_playback_command(
        self,
        command: str,
        *args: Any,
    ) -> dict[str, Any]:
        client = self._ensure_connection()

        if client is None:
            return {
                "success": False,
                "connected": False,
                "state": "stop",
                "error": "MPD ist nicht erreichbar.",
            }

        with self._lock:
            try:
                getattr(client, command)(*args)
                status = client.status()
            except (CommandError, MPDConnectionError, ProtocolError, OSError) as error:
                self._disconnect_unlocked()

                return {
                    "success": False,
                    "connected": False,
                    "state": "stop",
                    "error": str(error),
                }

        return {
            "success": True,
            "connected": True,
            "state": status.get("state", "stop"),
        }

    @staticmethod
    def _offline_status() -> dict[str, Any]:
        return {
            "connected": False,
            "state": "stop",
            "volume": 0,
            "elapsed": 0,
            "duration": 0,
        }

    @staticmethod
    def _empty_track() -> dict[str, Any]:
        return {
            "title": "",
            "artist": "",
            "album": "",
            "file": "",
            "cover_url": "",
            "duration": 0,
            "elapsed": 0,
        }

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


mpd_service = MPDService()