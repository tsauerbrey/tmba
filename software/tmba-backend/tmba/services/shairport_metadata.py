"""Shairport Sync metadata observer for TMBA.

Shairport Sync writes XML-style metadata items to a FIFO. This module parses
those items in a background thread and synchronises ``airplay_service``.
"""
from __future__ import annotations

import base64
import logging
import os
import re
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from tmba.services.airplay_service import airplay_service

LOGGER = logging.getLogger(__name__)
DEFAULT_FIFO = Path(os.environ.get("TMBA_SHAIRPORT_METADATA_FIFO", "/run/tmba/shairport-metadata"))
_ITEM_PATTERN = re.compile(br"<item>.*?</item>", re.DOTALL)


@dataclass(frozen=True)
class MetadataItem:
    item_type: str
    code: str
    payload: bytes

    @property
    def text(self) -> str:
        return self.payload.decode("utf-8", errors="replace").strip("\x00\r\n ")


def _decode_fourcc(value: str) -> str:
    """Decode Shairport Sync's hexadecimal four-character type/code values.

    Shairport Sync normally emits values such as ``73736e63`` (``ssnc``)
    and ``70626567`` (``pbeg``). Keeping support for literal four-character
    values makes tests and older variants work as well.
    """
    normalized = value.strip()
    if len(normalized) == 8:
        try:
            decoded = bytes.fromhex(normalized).decode("ascii")
        except (ValueError, UnicodeDecodeError):
            return normalized
        if len(decoded) == 4:
            return decoded
    return normalized


def parse_metadata_item(raw_item: bytes) -> MetadataItem | None:
    """Parse one XML metadata item emitted by Shairport Sync."""
    try:
        root = ET.fromstring(raw_item)
        item_type = _decode_fourcc(root.findtext("type") or "")
        code = _decode_fourcc(root.findtext("code") or "")
        encoded = (root.findtext("data") or "").strip()
        payload = base64.b64decode(encoded, validate=False) if encoded else b""
    except (ET.ParseError, ValueError) as exc:
        LOGGER.debug("Ungültiges Shairport-Metadatenelement: %s", exc)
        return None
    if not item_type or not code:
        return None
    return MetadataItem(item_type=item_type, code=code, payload=payload)


class ShairportMetadataObserver:
    """Read Shairport metadata continuously and update the AirPlay service."""

    def __init__(self, fifo_path: Path = DEFAULT_FIFO) -> None:
        self.fifo_path = fifo_path
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._buffer = b""
        self._title = ""
        self._artist = ""
        self._album = ""
        self._client_name = "AirPlay-Gerät"
        self._connected = False
        self._playing = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="shairport-metadata",
            daemon=True,
        )
        self._thread.start()
        LOGGER.info("Shairport-Metadatenbeobachter gestartet: %s", self.fifo_path)

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                with self.fifo_path.open("rb", buffering=0) as stream:
                    while not self._stop.is_set():
                        chunk = stream.read(8192)
                        if not chunk:
                            break
                        self.feed(chunk)
            except FileNotFoundError:
                LOGGER.warning("Metadaten-FIFO fehlt: %s", self.fifo_path)
            except PermissionError:
                LOGGER.exception("Kein Zugriff auf Metadaten-FIFO: %s", self.fifo_path)
            except OSError:
                LOGGER.exception("Fehler beim Lesen der Shairport-Metadaten")
            if not self._stop.wait(1.0):
                continue

    def feed(self, chunk: bytes) -> None:
        """Feed bytes into the parser; public to support deterministic tests."""
        self._buffer += chunk
        while True:
            match = _ITEM_PATTERN.search(self._buffer)
            if match is None:
                if len(self._buffer) > 2_000_000:
                    self._buffer = self._buffer[-65536:]
                return
            self._buffer = self._buffer[match.end():]
            item = parse_metadata_item(match.group(0))
            if item is not None:
                self._handle(item)

    def _handle(self, item: MetadataItem) -> None:
        key = (item.item_type, item.code)
        text = item.text

        if key == ("ssnc", "pbeg"):
            self._connected = True
            self._playing = True
            self._publish("playing")
            return
        if key == ("ssnc", "pend"):
            self._connected = False
            self._playing = False
            airplay_service.disconnect_client()
            return
        if key in {("ssnc", "prsm"), ("ssnc", "pres")}:
            self._connected = True
            self._playing = True
            self._publish("playing")
            return
        if key in {("ssnc", "prpa"), ("ssnc", "paus")}:
            self._connected = True
            self._playing = False
            self._publish("paused")
            return
        if key == ("core", "minm"):
            self._title = text
        elif key == ("core", "asar"):
            self._artist = text
        elif key == ("core", "asal"):
            self._album = text
        elif key in {("ssnc", "snam"), ("ssnc", "cname")} and text:
            self._client_name = text
        elif key == ("ssnc", "mden"):
            self._connected = True
            self._publish("playing" if self._playing else "idle")

    def _publish(self, playback_status: str) -> None:
        airplay_service.sync_state(
            connected=self._connected,
            client_name=self._client_name,
            playback_status=playback_status,
            title=self._title,
            artist=self._artist,
            album=self._album,
        )


shairport_metadata_observer = ShairportMetadataObserver()
