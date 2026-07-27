#!/usr/bin/env python3
"""Rounded, softly animated artwork display for TMBA."""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QWidget


class ArtworkWidget(QWidget):
    def __init__(
        self,
        artwork_path: str | Path = "/run/tmba/artwork/current.jpg",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.artwork_path = Path(artwork_path)
        self._pixmap: QPixmap | None = None
        self._signature: tuple[int, int] | None = None
        self.setFixedSize(218, 218)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 7)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)

        self._opacity = QGraphicsOpacityEffect(self)
        # Keep shadow as the widget effect; opacity animation is painted through
        # an internal value to avoid replacing the shadow effect.
        self._fade_value = 1.0
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(260)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_artwork)
        self._timer.start(500)
        self.refresh_artwork(force=True)

    def refresh_artwork(self, force: bool = False) -> None:
        try:
            stat = self.artwork_path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            signature = None
        if not force and signature == self._signature:
            return

        self._signature = signature
        loaded = None
        if signature is not None:
            candidate = QPixmap()
            if candidate.load(str(self.artwork_path)) and not candidate.isNull():
                loaded = candidate
        self._pixmap = loaded
        self._fade.stop()
        self.setWindowOpacity(0.25)
        self._fade.setStartValue(0.25)
        self._fade.setEndValue(1.0)
        self._fade.start()
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        target = self.rect().adjusted(3, 3, -3, -3)
        clip = QPainterPath()
        clip.addRoundedRect(target, 18, 18)
        painter.setClipPath(clip)
        painter.fillRect(target, QColor("#11151d"))

        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                target.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = target.x() + (target.width() - scaled.width()) // 2
            y = target.y() + (target.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            self._placeholder(painter, target)

    def _placeholder(self, painter: QPainter, target) -> None:
        painter.fillRect(target, QColor("#151923"))
        painter.setPen(QColor("#7fa9ff"))
        font = QFont("Sans Serif", 34, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        painter.setFont(font)
        painter.drawText(target.adjusted(0, -18, 0, 0), Qt.AlignmentFlag.AlignCenter, "TMBA")
        painter.setPen(QColor("#8f99ad"))
        painter.setFont(QFont("Sans Serif", 12, QFont.Weight.DemiBold))
        painter.drawText(target.adjusted(0, 62, 0, 0), Qt.AlignmentFlag.AlignCenter, "BEREIT FÜR MUSIK")
