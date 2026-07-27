"""Shairport Sync metadata observer for TMBA.

Shairport Sync writes XML-style metadata items to a FIFO. This module parses
those items in a background thread, synchronises ``airplay_service`` and stores
AirPlay cover artwork atomically for the native TMBA user interface.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import threading
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from tmba.services.airplay_service import airplay_service

LOGGER = logging.getLogger(__name__)

DEFAULT_FIFO = Path(
    os.environ.get(
        "TMBA_SHAIRPORT_METADATA_FIFO",
        "/run/tmba/shairport-metadata",
    )
)
DEFAULT_ARTWORK_DIRECTORY = Path(
    os.environ.get(
        "TMBA_AIRPLAY_ARTWORK_DIRECTORY",
        "/run/tmba/artwork",
    )
)
DEFAULT_ARTWORK_FILE = DEFAULT_ARTWORK_DIRECTORY / "current.jpg"

_ITEM_PATTERN = re.compile(br"<item>.*?</item>", re.DOTALL)
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class MetadataItem:
    item_type: str
    code: str
    payload: bytes

    @property
    def text(self) -> str:
        return self.payload.decode(
            "utf-8",
            errors="replace",
        ).strip("\x00\r\n ")


def _decode_fourcc(value: str) -> str:
    """Decode hexadecimal Shairport Sync type and code values."""
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
        payload = (
            base64.b64decode(encoded, validate=False)
            if encoded
            else b""
        )
    except (ET.ParseError, ValueError) as exc:
        LOGGER.debug(
            "Ungültiges Shairport-Metadatenelement: %s",
            exc,
        )
        return None

    if not item_type or not code:
        return None

    return MetadataItem(
        item_type=item_type,
        code=code,
        payload=payload,
    )


class AirPlayArtworkStore:
    """Store received artwork atomically and avoid duplicate writes."""

    def __init__(
        self,
        artwork_file: Path = DEFAULT_ARTWORK_FILE,
    ) -> None:
        self.artwork_file = artwork_file
        self._digest = ""

    @staticmethod
    def is_supported_image(payload: bytes) -> bool:
        return (
            payload.startswith(_JPEG_MAGIC)
            or payload.startswith(_PNG_MAGIC)
        )

    def store(self, payload: bytes) -> bool:
        """Write new artwork atomically.

        Returns ``True`` only when the on-disk file was changed.
        """
        if not self.is_supported_image(payload):
            LOGGER.warning(
                "AirPlay-Cover verworfen: unbekanntes Bildformat "
                "(%d Byte)",
                len(payload),
            )
            return False

        digest = hashlib.sha256(payload).hexdigest()

        if digest == self._digest and self.artwork_file.exists():
            return False

        self.artwork_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_file = self.artwork_file.with_name(
            f".{self.artwork_file.name}.tmp"
        )

        try:
            with temporary_file.open("wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())

            os.replace(
                temporary_file,
                self.artwork_file,
            )
            self._digest = digest

            LOGGER.info(
                "AirPlay-Cover gespeichert: %s (%d Byte)",
                self.artwork_file,
                len(payload),
            )
            return True
        finally:
            try:
                temporary_file.unlink(missing_ok=True)
            except OSError:
                LOGGER.debug(
                    "Temporäre Coverdatei konnte nicht entfernt werden",
                    exc_info=True,
                )

    def clear(self) -> bool:
        """Remove stale artwork and reset the in-memory cache."""
        self._digest = ""

        try:
            self.artwork_file.unlink()
        except FileNotFoundError:
            return False
        except OSError:
            LOGGER.exception(
                "AirPlay-Cover konnte nicht entfernt werden: %s",
                self.artwork_file,
            )
            return False

        LOGGER.info(
            "Veraltetes AirPlay-Cover entfernt: %s",
            self.artwork_file,
        )
        return True


class ShairportMetadataObserver:
    """Read Shairport metadata and update AirPlay state and artwork."""

    def __init__(
        self,
        fifo_path: Path = DEFAULT_FIFO,
        artwork_store: AirPlayArtworkStore | None = None,
    ) -> None:
        self.fifo_path = fifo_path
        self.artwork_store = (
            artwork_store
            if artwork_store is not None
            else AirPlayArtworkStore()
        )
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

        LOGGER.info(
            "Shairport-Metadatenbeobachter gestartet: %s",
            self.fifo_path,
        )

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                with self.fifo_path.open(
                    "rb",
                    buffering=0,
                ) as stream:
                    while not self._stop.is_set():
                        chunk = stream.read(8192)

                        if not chunk:
                            break

                        self.feed(chunk)
            except FileNotFoundError:
                LOGGER.warning(
                    "Metadaten-FIFO fehlt: %s",
                    self.fifo_path,
                )
            except PermissionError:
                LOGGER.exception(
                    "Kein Zugriff auf Metadaten-FIFO: %s",
                    self.fifo_path,
                )
            except OSError:
                LOGGER.exception(
                    "Fehler beim Lesen der Shairport-Metadaten"
                )

            self._stop.wait(1.0)

    def feed(self, chunk: bytes) -> None:
        """Feed bytes into the parser for deterministic tests."""
        self._buffer += chunk

        while True:
            match = _ITEM_PATTERN.search(self._buffer)

            if match is None:
                if len(self._buffer) > 8_000_000:
                    self._buffer = self._buffer[-65536:]
                return

            self._buffer = self._buffer[match.end():]
            item = parse_metadata_item(match.group(0))

            if item is not None:
                self._handle(item)

    def _handle(self, item: MetadataItem) -> None:
        key = (
            item.item_type.lower(),
            item.code.lower(),
        )
        text = item.text

        if key == ("ssnc", "pbeg"):
            self._connected = True
            self._playing = True
            self.artwork_store.clear()
            self._publish("playing")
            return

        if key == ("ssnc", "pend"):
            self._connected = False
            self._playing = False
            self.artwork_store.clear()
            airplay_service.disconnect_client()
            return

        if key in {
            ("ssnc", "prsm"),
            ("ssnc", "pres"),
        }:
            self._connected = True
            self._playing = True
            self._publish("playing")
            return

        if key in {
            ("ssnc", "prpa"),
            ("ssnc", "paus"),
        }:
            self._connected = True
            self._playing = False
            self._publish("paused")
            return

        if key == ("ssnc", "pict"):
            if item.payload:
                self.artwork_store.store(item.payload)
            else:
                self.artwork_store.clear()
            return

        if key == ("core", "minm"):
            if text != self._title:
                # A new title must never temporarily show the old cover.
                self.artwork_store.clear()
            self._title = text
        elif key == ("core", "asar"):
            self._artist = text
        elif key == ("core", "asal"):
            self._album = text
        elif (
            key in {
                ("ssnc", "snam"),
                ("ssnc", "cname"),
            }
            and text
        ):
            self._client_name = text
        elif key == ("ssnc", "mden"):
            self._connected = True
            self._publish(
                "playing" if self._playing else "idle"
            )

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
