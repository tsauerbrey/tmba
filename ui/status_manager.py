#!/usr/bin/env python3
"""Central status polling and change distribution for the TMBA Qt UI."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

API_BASE = "http://127.0.0.1:8000"


@dataclass(frozen=True)
class AudioState:
    source: str = "none"
    state: str = "stopped"
    volume: int = 25
    muted: bool = False
    gain_db: float = -30.0
    volume_driver: str = "unknown"
    error: str | None = None


@dataclass(frozen=True)
class AirPlayState:
    available: bool = False
    status: str = "idle"
    title: str = "AirPlay"
    artist: str = "Warte auf Verbindung"
    album: str = ""


@dataclass(frozen=True)
class BluetoothState:
    available: bool = False
    status: str = "idle"
    title: str = "Bluetooth"
    artist: str = "Warte auf Verbindung"
    album: str = ""


class ApiClient:
    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            API_BASE + path,
            data=data,
            headers=headers,
            method=method,
        )

        with urllib.request.urlopen(request, timeout=1.5) as response:
            return json.loads(response.read().decode("utf-8"))

    def audio_status(self) -> AudioState:
        raw = self._request("GET", "/audio/status")

        return AudioState(
            source=str(raw.get("source", "none")),
            state=str(raw.get("state", "stopped")),
            volume=int(raw.get("volume", 25)),
            muted=bool(raw.get("muted", False)),
            gain_db=float(raw.get("gain_db", -30.0)),
            volume_driver=str(
                (raw.get("volume_control") or {}).get(
                    "driver",
                    "unknown",
                )
            ),
            error=raw.get("error"),
        )

    def airplay_status(self) -> AirPlayState:
        raw = self._request("GET", "/airplay/status")
        track = raw.get("track") or {}

        return AirPlayState(
            available=bool(raw.get("available", False)),
            status=str(raw.get("status", "idle")),
            title=str(track.get("title") or "AirPlay"),
            artist=str(
                track.get("artist") or "Warte auf Verbindung"
            ),
            album=str(track.get("album") or ""),
        )

    def bluetooth_status(self) -> BluetoothState:
        raw = self._request("GET", "/bluetooth/status")
        track = raw.get("track") or {}

        return BluetoothState(
            available=bool(raw.get("available", False)),
            status=str(raw.get("status", "idle")),
            title=str(track.get("title") or "Bluetooth"),
            artist=str(
                track.get("artist") or "Warte auf Verbindung"
            ),
            album=str(track.get("album") or ""),
        )

    def set_volume(self, value: int) -> None:
        self._request(
            "POST",
            "/audio/volume",
            {"volume": int(value)},
        )

    def set_muted(self, muted: bool) -> None:
        self._request(
            "POST",
            "/audio/mute",
            {"muted": bool(muted)},
        )

    def testtone(self) -> None:
        self._request(
            "POST",
            "/audio/testtone",
            {
                "frequency_hz": 440,
                "duration_seconds": 1.0,
                "amplitude": 0.20,
            },
        )


class StatusManager(QObject):
    """Poll the backend once per cycle and emit typed snapshots."""

    status_changed = Signal(object, object, object)
    connection_changed = Signal(bool, str)

    def __init__(
        self,
        interval_ms: int = 1000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.api = ApiClient()
        self.audio = AudioState()
        self.airplay = AirPlayState()
        self.bluetooth = BluetoothState()
        self.connected = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(interval_ms)

    def start(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        try:
            audio = self.api.audio_status()
            airplay = self.api.airplay_status()
            bluetooth = self.api.bluetooth_status()

        except (
            OSError,
            ValueError,
            urllib.error.URLError,
            json.JSONDecodeError,
        ) as exc:
            message = str(exc)

            if self.connected:
                self.connected = False

            self.connection_changed.emit(False, message)
            return

        self.audio = audio
        self.airplay = airplay
        self.bluetooth = bluetooth

        if not self.connected:
            self.connected = True
            self.connection_changed.emit(True, "")

        self.status_changed.emit(
            audio,
            airplay,
            bluetooth,
        )
