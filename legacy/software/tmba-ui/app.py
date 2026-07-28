#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

API_BASE = "http://127.0.0.1:8000"


@dataclass
class AudioState:
    source: str = "none"
    state: str = "stopped"
    volume: int = 25
    muted: bool = False
    gain_db: float = -30.0
    error: str | None = None


@dataclass
class AirPlayState:
    available: bool = False
    status: str = "idle"
    title: str = "AirPlay"
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
        with urllib.request.urlopen(request, timeout=2.5) as response:
            return json.loads(response.read().decode("utf-8"))

    def status(self) -> AudioState:
        raw = self._request("GET", "/audio/status")
        return AudioState(
            source=str(raw.get("source", "none")),
            state=str(raw.get("state", "stopped")),
            volume=int(raw.get("volume", 25)),
            muted=bool(raw.get("muted", False)),
            gain_db=float(raw.get("gain_db", -30.0)),
            error=raw.get("error"),
        )

    def airplay_status(self) -> AirPlayState:
        raw = self._request("GET", "/airplay/status")
        track = raw.get("track") or {}
        return AirPlayState(
            available=bool(raw.get("available", False)),
            status=str(raw.get("status", "idle")),
            title=str(track.get("title") or "AirPlay"),
            artist=str(track.get("artist") or "Warte auf Verbindung"),
            album=str(track.get("album") or ""),
        )

    def set_volume(self, value: int) -> None:
        self._request("POST", "/audio/volume", {"volume": int(value)})

    def set_muted(self, muted: bool) -> None:
        self._request("POST", "/audio/mute", {"muted": bool(muted)})

    def testtone(self) -> None:
        self._request(
            "POST",
            "/audio/testtone",
            {"frequency_hz": 440, "duration_seconds": 1.0, "amplitude": 0.20},
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.api = ApiClient()
        self.current = AudioState()
        self._slider_dragging = False

        self.setWindowTitle("TMBA")
        self.setFixedSize(800, 480)
        self.setCursor(Qt.CursorShape.BlankCursor)

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(28, 18, 28, 20)
        page.setSpacing(12)

        # Kopfzeile
        header = QHBoxLayout()
        header.setSpacing(12)
        brand = QLabel("TMBA", objectName="brand")
        brand.setFont(QFont("Sans Serif", 26, QFont.Weight.Bold))
        header.addWidget(brand)
        header.addStretch(1)
        self.backend_dot = QLabel("●", objectName="backendDot")
        self.backend_text = QLabel("Backend wird verbunden", objectName="backendText")
        header.addWidget(self.backend_dot)
        header.addWidget(self.backend_text)
        page.addLayout(header)

        # Now-Playing-Karte
        card = QFrame(objectName="nowPlayingCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 18, 28, 18)
        card_layout.setSpacing(4)

        card_header = QHBoxLayout()
        self.source_badge = QLabel("AIRPLAY", objectName="sourceBadge")
        self.source_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_badge.setFixedHeight(32)
        self.status_badge = QLabel("BEREIT", objectName="statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedHeight(32)
        card_header.addWidget(self.source_badge)
        card_header.addStretch(1)
        card_header.addWidget(self.status_badge)
        card_layout.addLayout(card_header)

        card_layout.addStretch(1)
        self.title_label = QLabel("Bereit für Musik", objectName="title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(86)
        card_layout.addWidget(self.title_label)

        self.artist_label = QLabel(
            "TMBA auf Mac, iPhone oder iPad auswählen",
            objectName="artist",
        )
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist_label.setWordWrap(True)
        self.artist_label.setMaximumHeight(54)
        card_layout.addWidget(self.artist_label)

        self.album_label = QLabel("", objectName="album")
        self.album_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_label.setWordWrap(True)
        self.album_label.setMaximumHeight(42)
        card_layout.addWidget(self.album_label)
        card_layout.addStretch(1)
        page.addWidget(card, 1)

        # Lautstärke
        volume_panel = QFrame(objectName="volumePanel")
        volume_layout = QHBoxLayout(volume_panel)
        volume_layout.setContentsMargins(14, 8, 14, 8)
        volume_layout.setSpacing(14)

        self.minus = QPushButton("−", objectName="roundButton")
        self.minus.clicked.connect(lambda: self.change_volume(-2))
        volume_layout.addWidget(self.minus)

        self.slider = QSlider(Qt.Orientation.Horizontal, objectName="volumeSlider")
        self.slider.setRange(0, 90)
        self.slider.setSingleStep(2)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        volume_layout.addWidget(self.slider, 1)

        self.plus = QPushButton("+", objectName="roundButton")
        self.plus.clicked.connect(lambda: self.change_volume(2))
        volume_layout.addWidget(self.plus)

        self.volume_label = QLabel("25 %", objectName="volume")
        self.volume_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.volume_label.setMinimumWidth(92)
        volume_layout.addWidget(self.volume_label)
        page.addWidget(volume_panel)

        # Aktionen
        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.mute_button = QPushButton("Stumm", objectName="actionButton")
        self.mute_button.clicked.connect(self.toggle_mute)
        actions.addWidget(self.mute_button)
        self.test_button = QPushButton("Testton", objectName="actionButton")
        self.test_button.clicked.connect(self.play_testtone)
        actions.addWidget(self.test_button)
        page.addLayout(actions)

        self.setStyleSheet(
            """
            QWidget#root {
                background: #090b10;
                color: #f5f7fb;
            }
            QLabel#brand {
                color: #ffffff;
                letter-spacing: 3px;
            }
            QLabel#backendDot {
                color: #8b94a7;
                font-size: 17px;
            }
            QLabel#backendText {
                color: #9ba4b7;
                font-size: 15px;
                font-weight: 600;
            }
            QFrame#nowPlayingCard {
                background: #151923;
                border: 1px solid #2a3140;
                border-radius: 20px;
            }
            QLabel#sourceBadge {
                min-width: 102px;
                padding: 0 14px;
                border-radius: 16px;
                background: #1e3153;
                color: #8eb8ff;
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 2px;
            }
            QLabel#statusBadge {
                min-width: 118px;
                padding: 0 14px;
                border-radius: 16px;
                background: #29253c;
                color: #d8b4fe;
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#title {
                color: #ffffff;
                font-size: 32px;
                font-weight: 800;
            }
            QLabel#artist {
                color: #d1d7e4;
                font-size: 21px;
                font-weight: 650;
            }
            QLabel#album {
                color: #8f99ad;
                font-size: 16px;
            }
            QFrame#volumePanel {
                background: #11151d;
                border: 1px solid #252c39;
                border-radius: 17px;
            }
            QLabel#volume {
                color: #ffffff;
                font-size: 25px;
                font-weight: 800;
            }
            QPushButton#actionButton {
                min-height: 52px;
                background: #202633;
                border: 1px solid #343d4f;
                border-radius: 14px;
                color: #ffffff;
                font-size: 19px;
                font-weight: 700;
            }
            QPushButton#actionButton:pressed {
                background: #30394a;
            }
            QPushButton#roundButton {
                min-width: 52px;
                max-width: 52px;
                min-height: 52px;
                max-height: 52px;
                border-radius: 26px;
                background: #202633;
                border: 1px solid #343d4f;
                color: #ffffff;
                font-size: 30px;
                font-weight: 500;
            }
            QPushButton#roundButton:pressed {
                background: #30394a;
            }
            QSlider#volumeSlider::groove:horizontal {
                height: 11px;
                background: #2a3040;
                border-radius: 5px;
            }
            QSlider#volumeSlider::sub-page:horizontal {
                background: #7fa9ff;
                border-radius: 5px;
            }
            QSlider#volumeSlider::handle:horizontal {
                width: 32px;
                margin: -11px 0;
                background: #ffffff;
                border: 2px solid #7fa9ff;
                border-radius: 16px;
            }
            """
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def _set_backend_state(self, connected: bool) -> None:
        if connected:
            self.backend_dot.setStyleSheet("color: #4ade80;")
            self.backend_text.setText("Backend verbunden")
            self.backend_text.setStyleSheet("color: #a7f3d0;")
        else:
            self.backend_dot.setStyleSheet("color: #fb7185;")
            self.backend_text.setText("Backend nicht erreichbar")
            self.backend_text.setStyleSheet("color: #fecdd3;")

    def _set_status_badge(self, text: str, foreground: str, background: str) -> None:
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(
            f"color: {foreground}; background: {background};"
            "min-width: 118px; padding: 0 14px; border-radius: 16px;"
            "font-size: 14px; font-weight: 800; letter-spacing: 1px;"
        )

    def refresh(self) -> None:
        try:
            state = self.api.status()
            airplay = self.api.airplay_status()
            self.current = state
            self._set_backend_state(True)
            if not self._slider_dragging:
                self.slider.setValue(state.volume)
            self.volume_label.setText("STUMM" if state.muted else f"{state.volume} %")
            self.mute_button.setText("Ton an" if state.muted else "Stumm")

            if state.error:
                self._set_status_badge("AUDIOFEHLER", "#fecaca", "#4c1d2b")
                self.title_label.setText("Audiofehler")
                self.artist_label.setText(str(state.error))
                self.album_label.clear()
            else:
                self.show_airplay(airplay)
        except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self._set_backend_state(False)
            self._set_status_badge("OFFLINE", "#fecaca", "#4c1d2b")
            self.title_label.setText("TMBA wird gestartet")
            self.artist_label.setText("Backend ist noch nicht erreichbar")
            self.album_label.setText(str(exc))

    def show_airplay(self, airplay: AirPlayState) -> None:
        if not airplay.available:
            self._set_status_badge("BEREIT", "#d8b4fe", "#33275a")
            self.title_label.setText("Bereit für Musik")
            self.artist_label.setText("TMBA auf Mac, iPhone oder iPad auswählen")
            self.album_label.setText("AirPlay")
            return

        if airplay.status == "playing":
            self._set_status_badge("▶ WIEDERGABE", "#bbf7d0", "#14532d")
        elif airplay.status == "paused":
            self._set_status_badge("Ⅱ PAUSIERT", "#fde68a", "#59450b")
        else:
            self._set_status_badge("VERBUNDEN", "#bfdbfe", "#1e3a5f")

        title = airplay.title.strip()
        artist = airplay.artist.strip()
        album = airplay.album.strip()
        self.title_label.setText(title if title and title != "AirPlay" else "AirPlay verbunden")
        self.artist_label.setText(artist if artist else "Unbekannter Interpret")
        self.album_label.setText(album if album else "")

    def _on_slider_pressed(self) -> None:
        self._slider_dragging = True

    def _on_slider_released(self) -> None:
        self._slider_dragging = False
        self._set_volume(self.slider.value())

    def change_volume(self, delta: int) -> None:
        self._set_volume(max(0, min(90, self.current.volume + delta)))

    def _set_volume(self, value: int) -> None:
        try:
            self.api.set_volume(value)
            self.current.volume = value
            self.slider.setValue(value)
            self.volume_label.setText(f"{value} %")
        except Exception as exc:  # UI must remain alive after a transient API error.
            self.artist_label.setText(f"Lautstärke konnte nicht gesetzt werden: {exc}")

    def toggle_mute(self) -> None:
        try:
            self.api.set_muted(not self.current.muted)
            self.current.muted = not self.current.muted
            self.refresh()
        except Exception as exc:
            self.artist_label.setText(f"Mute konnte nicht gesetzt werden: {exc}")

    def play_testtone(self) -> None:
        self.test_button.setEnabled(False)
        previous_artist = self.artist_label.text()
        self.artist_label.setText("Testton wird abgespielt …")
        QApplication.processEvents()
        try:
            self.api.testtone()
            self.artist_label.setText("Testton erfolgreich abgespielt")
        except Exception as exc:
            self.artist_label.setText(f"Testton fehlgeschlagen: {exc}")
        finally:
            self.test_button.setEnabled(True)
            QTimer.singleShot(1800, lambda: self.artist_label.setText(previous_artist))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("TMBA UI")
    window = MainWindow()
    window.showFullScreen()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
