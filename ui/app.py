#!/usr/bin/env python3
from __future__ import annotations
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)
from artwork_widget import ArtworkWidget
from status_manager import (
    AirPlayState,
    AudioState,
    BluetoothState,
    StatusManager,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.status_manager = StatusManager(parent=self)
        self.current = AudioState()
        self._slider_dragging = False

        self.setWindowTitle("TMBA")
        self.setFixedSize(800, 480)
        self.setCursor(Qt.CursorShape.BlankCursor)

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(20, 10, 20, 10)
        page.setSpacing(8)

        header = QHBoxLayout()
        brand = QLabel("TMBA", objectName="brand")
        brand.setFont(QFont("Sans Serif", 22, QFont.Weight.Bold))
        header.addWidget(brand)
        version = QLabel("v0.9.5 RC1.1", objectName="version")
        header.addWidget(version)
        header.addStretch()
        self.backend_dot = QLabel("●")
        self.backend_text = QLabel("Backend wird verbunden", objectName="backendText")
        header.addWidget(self.backend_dot)
        header.addWidget(self.backend_text)
        page.addLayout(header)

        card = QFrame(objectName="nowPlayingCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(15, 12, 17, 12)
        card_layout.setSpacing(22)
        self.artwork = ArtworkWidget()
        card_layout.addWidget(self.artwork)

        info = QVBoxLayout()
        info.setSpacing(5)
        badges = QHBoxLayout()
        self.source_badge = QLabel("AIRPLAY", objectName="sourceBadge")
        self.source_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_badge.setFixedHeight(28)
        self.status_badge = QLabel("BEREIT", objectName="statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedHeight(28)
        badges.addWidget(self.source_badge)
        badges.addStretch()
        badges.addWidget(self.status_badge)
        info.addLayout(badges)
        info.addStretch()
        self.title_label = QLabel("Bereit für Musik", objectName="title")
        self.title_label.setWordWrap(True)
        self.artist_label = QLabel("TMBA auf Mac, iPhone oder iPad auswählen", objectName="artist")
        self.artist_label.setWordWrap(True)
        self.album_label = QLabel("AirPlay", objectName="album")
        info.addWidget(self.title_label)
        info.addWidget(self.artist_label)
        info.addWidget(self.album_label)
        info.addStretch()
        card_layout.addLayout(info, 1)
        page.addWidget(card, 1)

        volume = QFrame(objectName="volumePanel")
        row = QHBoxLayout(volume)
        row.setContentsMargins(10, 5, 10, 5)
        row.setSpacing(10)
        self.minus = QPushButton("−", objectName="roundButton")
        self.minus.clicked.connect(lambda: self.change_volume(-2))
        self.slider = QSlider(Qt.Orientation.Horizontal, objectName="volumeSlider")
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(2)
        self.slider.sliderPressed.connect(self._slider_pressed)
        self.slider.sliderReleased.connect(self._slider_released)
        self.plus = QPushButton("+", objectName="roundButton")
        self.plus.clicked.connect(lambda: self.change_volume(2))
        self.volume_label = QLabel("25 %", objectName="volume")
        self.volume_label.setMinimumWidth(86)
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.mute_button = QPushButton("Stumm", objectName="muteButton")
        self.mute_button.clicked.connect(self.toggle_mute)
        row.addWidget(self.minus)
        row.addWidget(self.slider, 1)
        row.addWidget(self.plus)
        row.addWidget(self.volume_label)
        row.addWidget(self.mute_button)
        page.addWidget(volume)

        nav = QFrame(objectName="navBar")
        navrow = QHBoxLayout(nav)
        navrow.setContentsMargins(6, 4, 6, 4)
        navrow.setSpacing(6)
        self.airplay_nav = self._nav_button("◉  AirPlay", True)
        self.bluetooth_nav = self._nav_button("◆  Bluetooth", False)
        self.radio_nav = self._nav_button("●  Radio", False)
        self.settings_nav = self._nav_button("⚙  Einstellungen", False)
        self.bluetooth_nav.setEnabled(True)
        self.radio_nav.setEnabled(False)
        self.settings_nav.setEnabled(False)
        for button in (self.airplay_nav, self.bluetooth_nav, self.radio_nav, self.settings_nav):
            navrow.addWidget(button, 1)
        page.addWidget(nav)

        self.setStyleSheet(STYLE)
        self.status_manager.connection_changed.connect(self._connection)
        self.status_manager.status_changed.connect(self._status)
        self.status_manager.start()

    def _nav_button(self, text: str, active: bool) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("active", active)
        button.setObjectName("navButton")
        button.setMinimumHeight(38)
        return button

    def _connection(self, connected: bool, message: str) -> None:
        self.backend_dot.setStyleSheet(f"color: {'#4ade80' if connected else '#fb7185'};")
        self.backend_text.setText("Backend verbunden" if connected else "Backend nicht erreichbar")
        if not connected:
            self._badge("OFFLINE", "#fecaca", "#4c1d2b")

    def _status(
        self,
        state: AudioState,
        airplay: AirPlayState,
        bluetooth: BluetoothState,
    ) -> None:
        self.current = state

        if not self._slider_dragging:
            self.slider.setValue(state.volume)

        self.volume_label.setText(
            "STUMM" if state.muted else f"{state.volume} %"
        )
        self.mute_button.setText(
            "Ton an" if state.muted else "Stumm"
        )

        if state.error:
            self._badge(
                "AUDIOFEHLER",
                "#fecaca",
                "#4c1d2b",
            )
            self.title_label.setText("Audiofehler")
            self.artist_label.setText(str(state.error))
            self.album_label.setText("")
            return

        self._set_active_source(state.source)

        if state.source == "bluetooth":
            self._show_bluetooth(bluetooth)
        elif state.source == "airplay":
            self._show_airplay(airplay)
        else:
            self._show_ready()

    def _set_active_source(self, source: str) -> None:
        source = source.strip().lower()

        buttons = {
            "airplay": self.airplay_nav,
            "bluetooth": self.bluetooth_nav,
            "webradio": self.radio_nav,
        }

        for name, button in buttons.items():
            button.setProperty("active", name == source)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

        if source == "bluetooth":
            self.source_badge.setText("BLUETOOTH")
        elif source == "webradio":
            self.source_badge.setText("RADIO")
        elif source == "airplay":
            self.source_badge.setText("AIRPLAY")
        else:
            self.source_badge.setText("TMBA")

    def _show_ready(self) -> None:
        self._badge(
            "BEREIT",
            "#d8b4fe",
            "#33275a",
        )
        self.title_label.setText("Bereit für Musik")
        self.artist_label.setText(
            "AirPlay oder Bluetooth verbinden"
        )
        self.album_label.setText("TMBA")

    def _show_bluetooth(
        self,
        bluetooth: BluetoothState,
    ) -> None:
        if not bluetooth.available:
            self._badge(
                "BEREIT",
                "#d8b4fe",
                "#33275a",
            )
            self.title_label.setText(
                "Bluetooth bereit"
            )
            self.artist_label.setText(
                "TMBA in den Bluetooth-Einstellungen auswählen"
            )
            self.album_label.setText("Bluetooth")
            return

        if bluetooth.status == "playing":
            self._badge(
                "▶ WIEDERGABE",
                "#bbf7d0",
                "#14532d",
            )
        elif bluetooth.status == "paused":
            self._badge(
                "Ⅱ PAUSIERT",
                "#fde68a",
                "#59450b",
            )
        else:
            self._badge(
                "VERBUNDEN",
                "#bfdbfe",
                "#1e3a5f",
            )

        self.title_label.setText(
            bluetooth.title.strip()
            or "Bluetooth verbunden"
        )
        self.artist_label.setText(
            bluetooth.artist.strip()
            or "Bluetooth-Gerät"
        )
        self.album_label.setText(
            bluetooth.album.strip()
        )

    def _show_airplay(self, airplay: AirPlayState) -> None:
        # Playback status wins only while AirPlay is actually available.
        # This prevents the brief green WIEDERGABE state after disconnect.
        if not airplay.available:
            self._badge("BEREIT", "#d8b4fe", "#33275a")
            self.title_label.setText("Bereit für Musik")
            self.artist_label.setText("TMBA auf Mac, iPhone oder iPad auswählen")
            self.album_label.setText("AirPlay")
            return
        if airplay.status == "playing":
            self._badge("▶ WIEDERGABE", "#bbf7d0", "#14532d")
        elif airplay.status == "paused":
            self._badge("Ⅱ PAUSIERT", "#fde68a", "#59450b")
        else:
            self._badge("VERBUNDEN", "#bfdbfe", "#1e3a5f")
        self.title_label.setText(airplay.title.strip() or "AirPlay verbunden")
        self.artist_label.setText(airplay.artist.strip() or "Unbekannter Interpret")
        self.album_label.setText(airplay.album.strip())

    def _badge(self, text: str, fg: str, bg: str) -> None:
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(
            f"color:{fg};background:{bg};min-width:112px;padding:0 12px;"
            "border-radius:14px;font-size:12px;font-weight:800;"
        )

    def _slider_pressed(self) -> None:
        self._slider_dragging = True

    def _slider_released(self) -> None:
        self._slider_dragging = False
        self._set_volume(self.slider.value())

    def change_volume(self, delta: int) -> None:
        self._set_volume(max(0, min(100, self.current.volume + delta)))

    def _set_volume(self, value: int) -> None:
        try:
            self.status_manager.api.set_volume(value)
            self.slider.setValue(value)
            self.volume_label.setText(f"{value} %")
        except Exception as exc:
            self.artist_label.setText(f"Lautstärke konnte nicht gesetzt werden: {exc}")

    def toggle_mute(self) -> None:
        try:
            self.status_manager.api.set_muted(not self.current.muted)
        except Exception as exc:
            self.artist_label.setText(f"Mute konnte nicht gesetzt werden: {exc}")


STYLE = """
QWidget#root { background:#090b10; color:#f5f7fb; }
QLabel#brand { color:#fff; letter-spacing:3px; }
QLabel#version { color:#68748a; font-size:12px; font-weight:700; padding-top:5px; }
QLabel#backendText { color:#9ba4b7; font-size:13px; font-weight:600; }
QFrame#nowPlayingCard { background:#151923; border:1px solid #2a3140; border-radius:20px; }
QLabel#sourceBadge { min-width:96px; padding:0 12px; border-radius:14px;
 background:#1e3153; color:#8eb8ff; font-size:12px; font-weight:800; letter-spacing:2px; }
QLabel#statusBadge { min-width:112px; padding:0 12px; border-radius:14px;
 background:#33275a; color:#d8b4fe; font-size:12px; font-weight:800; }
QLabel#title { color:#fff; font-size:27px; font-weight:800; }
QLabel#artist { color:#d1d7e4; font-size:19px; font-weight:650; }
QLabel#album { color:#8f99ad; font-size:15px; }
QFrame#volumePanel { background:#11151d; border:1px solid #252c39; border-radius:16px; }
QLabel#volume { color:#fff; font-size:22px; font-weight:800; }
QPushButton#roundButton { min-width:42px; max-width:42px; min-height:42px; max-height:42px;
 border-radius:21px; background:#202633; border:1px solid #343d4f; color:#fff; font-size:25px; }
QPushButton#muteButton { min-width:88px; min-height:40px; border-radius:12px;
 background:#202633; border:1px solid #343d4f; color:#fff; font-size:16px; font-weight:700; }
QSlider#volumeSlider::groove:horizontal { height:10px; background:#2a3040; border-radius:5px; }
QSlider#volumeSlider::sub-page:horizontal { background:#7fa9ff; border-radius:5px; }
QSlider#volumeSlider::handle:horizontal { width:28px; margin:-9px 0; background:#fff;
 border:2px solid #7fa9ff; border-radius:14px; }
QFrame#navBar { background:#10141c; border:1px solid #252c39; border-radius:15px; }
QPushButton#navButton { border:0; border-radius:10px; background:transparent;
 color:#747f94; font-size:14px; font-weight:700; }
QPushButton#navButton[active="true"] { background:#1d2d4b; color:#9fc1ff; }
QPushButton#navButton:disabled { color:#4b5362; }
"""

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("TMBA")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
