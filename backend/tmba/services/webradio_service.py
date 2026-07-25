from typing import Any

from tmba.services.base_source_service import BaseSourceService
from tmba.services.mpd_service import mpd_service
from tmba.core.event_bus import event_bus


class WebradioService(BaseSourceService):
    """Verwaltet Webradio-Wiedergabe über MPD."""

    def __init__(self) -> None:
        super().__init__(
            source_name="webradio",
            default_title="Webradio",
            default_artist="Sender auswählen",
            default_album="TMBA-OS",
        )

    def play_station(
        self,
        url: str,
        station_name: str = "",
    ) -> dict[str, Any]:
        """Lädt und startet einen Webradio-Sender."""

        normalized_station_name = (
            station_name.strip() or "Webradio"
        )

        mpd_result = mpd_service.load_stream(
            url=url,
            station_name=normalized_station_name,
        )

        if not mpd_result.get("success"):
            return {
                "success": False,
                "mpd": mpd_result,
                "webradio": self.get_status(),
            }

        self.session_started()

        self.update_metadata(
            title=normalized_station_name,
            artist="Live",
            album="Webradio",
            cover_url="",
            duration=0,
            elapsed=0,
        )

        self.set_playback_status("playing")

        return {
            "success": True,
            "mpd": mpd_result,
            "webradio": self.get_status(),
        }

    def play(self) -> dict[str, Any]:
        """Setzt eine pausierte Webradio-Wiedergabe fort."""

        mpd_result = mpd_service.play()

        if mpd_result.get("success"):
            self.set_playback_status("playing")

        return {
            "success": bool(mpd_result.get("success")),
            "mpd": mpd_result,
            "webradio": self.get_status(),
        }

    def pause(self) -> dict[str, Any]:
        """Pausiert die Webradio-Wiedergabe."""

        mpd_result = mpd_service.pause()

        if mpd_result.get("success"):
            self.set_playback_status("paused")

        return {
            "success": bool(mpd_result.get("success")),
            "mpd": mpd_result,
            "webradio": self.get_status(),
        }

    def stop(self) -> dict[str, Any]:
        """Stoppt Webradio und beendet die Quellensitzung."""

        mpd_result = mpd_service.stop()

        if mpd_result.get("success"):
            self.session_ended()

        return {
            "success": bool(mpd_result.get("success")),
            "mpd": mpd_result,
            "webradio": self.get_status(),
        }

    def set_volume(self, volume: int) -> dict[str, Any]:
        """Setzt die MPD-Lautstärke für Webradio."""

        mpd_result = mpd_service.set_volume(volume)

        if mpd_result.get("success"):
            event_bus.publish(
                "player.volume_changed",
                {
                    "source": "webradio",
                    "volume": mpd_result.get("volume", volume),
                },
            )

        return {
            "success": bool(mpd_result.get("success")),
            "mpd": mpd_result,
            "webradio": self.get_status(),
        }

    def sync_from_mpd(self) -> dict[str, Any]:
        """Übernimmt Status, Lautstärke und Metadaten aus MPD."""

        mpd_status = mpd_service.get_status()
        mpd_track = mpd_service.get_current_track()

        if not mpd_status.get("connected"):
            return {
                "success": False,
                "mpd": mpd_status,
                "webradio": self.get_status(),
                "error": "MPD ist nicht erreichbar.",
            }

        state = str(
            mpd_status.get("state", "stop")
        ).strip().lower()

        status_mapping = {
            "play": "playing",
            "pause": "paused",
            "stop": "idle",
        }

        playback_status = status_mapping.get(state, "idle")

        # Nach einem Backend-Neustart läuft MPD eventuell weiter,
        # während der WebradioService seinen Zustand verloren hat.
        # Dann muss die Webradio-Sitzung wiederhergestellt werden.
        if state in {"play", "pause"}:
            current_status = self.get_status()

            if not current_status.get("available", False):
                self.session_started()

        elif state == "stop":
            current_status = self.get_status()

            if current_status.get("available", False):
                self.session_ended()

        volume = mpd_status.get("volume")

        if volume is not None:
            event_bus.publish(
                "player.volume_changed",
                {
                    "source": "webradio",
                    "volume": volume,
                },
            )

        current_track = self.get_status()["track"]

        title = (
            str(mpd_track.get("title") or "").strip()
            or str(current_track.get("title") or "Webradio")
        )

        artist = (
            str(mpd_track.get("artist") or "").strip()
            or "Live"
        )

        album = (
            str(mpd_track.get("album") or "").strip()
            or "Webradio"
        )

        self.update_metadata(
            title=title,
            artist=artist,
            album=album,
            cover_url=str(
                mpd_track.get("cover_url") or ""
            ),
            duration=mpd_track.get("duration", 0),
            elapsed=mpd_track.get("elapsed", 0),
        )

        self.set_playback_status(playback_status)

        return {
            "success": True,
            "mpd": {
                "status": mpd_status,
                "track": mpd_track,
            },
            "webradio": self.get_status(),
        }


webradio_service = WebradioService()