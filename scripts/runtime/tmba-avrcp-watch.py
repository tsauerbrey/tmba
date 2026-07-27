#!/usr/bin/env python3
"""Synchronisiert BlueZ-AVRCP-Daten mit dem TMBA-Backend."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)


API_BASE = "http://127.0.0.1:8000"

BLUEZ_SERVICE = "org.bluez"
OBJECT_MANAGER_INTERFACE = "org.freedesktop.DBus.ObjectManager"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
MEDIA_PLAYER_INTERFACE = "org.bluez.MediaPlayer1"
DEVICE_INTERFACE = "org.bluez.Device1"

POSITION_INTERVAL_SECONDS = 1


def plain(value: Any) -> Any:
    """Wandelt dbus-python-Typen in normale Python-Typen um."""

    if isinstance(value, dbus.Dictionary):
        return {
            str(key): plain(item)
            for key, item in value.items()
        }

    if isinstance(value, (dbus.Array, list, tuple)):
        return [plain(item) for item in value]

    if isinstance(
        value,
        (
            dbus.String,
            dbus.ObjectPath,
        ),
    ):
        return str(value)

    if isinstance(
        value,
        (
            dbus.Boolean,
        ),
    ):
        return bool(value)

    if isinstance(
        value,
        (
            dbus.Byte,
            dbus.Int16,
            dbus.Int32,
            dbus.Int64,
            dbus.UInt16,
            dbus.UInt32,
            dbus.UInt64,
        ),
    ):
        return int(value)

    if isinstance(value, dbus.Double):
        return float(value)

    return value


def post(
    path: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    data = None
    headers = {
        "Accept": "application/json",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        API_BASE + path,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=3,
        ) as response:
            response.read()

        return True

    except (
        OSError,
        urllib.error.URLError,
        urllib.error.HTTPError,
    ) as error:
        print(
            f"TMBA-Backend nicht erreichbar: {error}",
            flush=True,
        )
        return False


def normalize_status(status: str) -> str:
    normalized = status.strip().lower()

    if normalized == "playing":
        return "playing"

    if normalized == "paused":
        return "paused"

    return "idle"


class AvrcpWatcher:
    def __init__(self) -> None:
        self.bus = dbus.SystemBus()

        root_object = self.bus.get_object(
            BLUEZ_SERVICE,
            "/",
        )

        self.object_manager = dbus.Interface(
            root_object,
            OBJECT_MANAGER_INTERFACE,
        )

        self.player_path = ""
        self.player_properties: dbus.Interface | None = None
        self.device_name = "Bluetooth-Gerät"

        self.last_track: dict[str, Any] = {}
        self.last_status = ""
        self.last_position_ms = -1

        self.bus.add_signal_receiver(
            self._properties_changed,
            signal_name="PropertiesChanged",
            dbus_interface=PROPERTIES_INTERFACE,
            bus_name=BLUEZ_SERVICE,
            path_keyword="object_path",
        )

        self.bus.add_signal_receiver(
            self._interfaces_added,
            signal_name="InterfacesAdded",
            dbus_interface=OBJECT_MANAGER_INTERFACE,
            bus_name=BLUEZ_SERVICE,
        )

        self.bus.add_signal_receiver(
            self._interfaces_removed,
            signal_name="InterfacesRemoved",
            dbus_interface=OBJECT_MANAGER_INTERFACE,
            bus_name=BLUEZ_SERVICE,
        )

    def start(self) -> None:
        print(
            "TMBA AVRCP-Watcher gestartet",
            flush=True,
        )

        self._find_player()

        GLib.timeout_add_seconds(
            POSITION_INTERVAL_SECONDS,
            self._poll_position,
        )

        GLib.MainLoop().run()

    def _find_player(self) -> None:
        try:
            managed_objects = self.object_manager.GetManagedObjects()
        except dbus.DBusException as error:
            print(
                f"BlueZ-Objekte konnten nicht gelesen werden: {error}",
                flush=True,
            )
            return

        for object_path, interfaces in managed_objects.items():
            if MEDIA_PLAYER_INTERFACE in interfaces:
                self._attach_player(str(object_path))
                return

        print(
            "Noch kein AVRCP-Player verfügbar",
            flush=True,
        )

    def _attach_player(self, object_path: str) -> None:
        if object_path == self.player_path:
            return

        try:
            player_object = self.bus.get_object(
                BLUEZ_SERVICE,
                object_path,
            )

            properties = dbus.Interface(
                player_object,
                PROPERTIES_INTERFACE,
            )

            player_values = plain(
                properties.GetAll(MEDIA_PLAYER_INTERFACE)
            )

        except dbus.DBusException as error:
            print(
                f"AVRCP-Player konnte nicht geöffnet werden: {error}",
                flush=True,
            )
            return

        self.player_path = object_path
        self.player_properties = properties
        self.device_name = self._read_device_name(
            player_values.get("Device", "")
        )

        self.last_track = {}
        self.last_status = ""
        self.last_position_ms = -1

        print(
            f"AVRCP-Player erkannt: {object_path}",
            flush=True,
        )
        print(
            f"Bluetooth-Gerät: {self.device_name}",
            flush=True,
        )

        self._send_track(
            player_values.get("Track") or {},
            force=True,
        )
        self._send_status(
            str(player_values.get("Status", "idle")),
            force=True,
        )
        self._send_position(
            int(player_values.get("Position", 0) or 0),
            force=True,
        )

    def _detach_player(self) -> None:
        if not self.player_path:
            return

        print(
            "AVRCP-Player entfernt",
            flush=True,
        )

        self.player_path = ""
        self.player_properties = None
        self.last_track = {}
        self.last_status = ""
        self.last_position_ms = -1

    def _read_device_name(self, device_path: str) -> str:
        if not device_path:
            return "Bluetooth-Gerät"

        try:
            device_object = self.bus.get_object(
                BLUEZ_SERVICE,
                device_path,
            )

            device_properties = dbus.Interface(
                device_object,
                PROPERTIES_INTERFACE,
            )

            values = plain(
                device_properties.GetAll(DEVICE_INTERFACE)
            )

            return str(
                values.get("Name")
                or values.get("Alias")
                or "Bluetooth-Gerät"
            )

        except dbus.DBusException:
            return "Bluetooth-Gerät"

    def _interfaces_added(
        self,
        object_path: dbus.ObjectPath,
        interfaces: dbus.Dictionary,
    ) -> None:
        interface_names = {
            str(name)
            for name in interfaces.keys()
        }

        if MEDIA_PLAYER_INTERFACE in interface_names:
            self._attach_player(str(object_path))

    def _interfaces_removed(
        self,
        object_path: dbus.ObjectPath,
        interfaces: dbus.Array,
    ) -> None:
        removed_interfaces = {
            str(name)
            for name in interfaces
        }

        if (
            str(object_path) == self.player_path
            and MEDIA_PLAYER_INTERFACE in removed_interfaces
        ):
            self._detach_player()

    def _properties_changed(
        self,
        interface_name: str,
        changed_properties: dbus.Dictionary,
        invalidated_properties: dbus.Array,
        object_path: str = "",
    ) -> None:
        if str(interface_name) != MEDIA_PLAYER_INTERFACE:
            return

        if str(object_path) != self.player_path:
            return

        changed = plain(changed_properties)

        if "Track" in changed:
            self._send_track(
                changed.get("Track") or {},
            )

        if "Status" in changed:
            self._send_status(
                str(changed.get("Status", "idle")),
            )

        if "Position" in changed:
            self._send_position(
                int(changed.get("Position", 0) or 0),
            )

    def _send_track(
        self,
        track: dict[str, Any],
        *,
        force: bool = False,
    ) -> None:
        normalized_track = {
            str(key): plain(value)
            for key, value in track.items()
        }

        if (
            not force
            and normalized_track == self.last_track
        ):
            return

        duration_ms = int(
            normalized_track.get("Duration", 0) or 0
        )

        payload = {
            "title": str(
                normalized_track.get("Title")
                or "Bluetooth"
            ),
            "artist": str(
                normalized_track.get("Artist")
                or self.device_name
            ),
            "album": str(
                normalized_track.get("Album")
                or "Bluetooth-Audio"
            ),
            "cover_url": "",
            "duration": duration_ms / 1000.0,
            "elapsed": max(
                0,
                self.last_position_ms,
            ) / 1000.0,
        }

        if post("/bluetooth/metadata", payload):
            self.last_track = normalized_track

            print(
                "Titel: "
                f"{payload['artist']} – {payload['title']}",
                flush=True,
            )

    def _send_status(
        self,
        status: str,
        *,
        force: bool = False,
    ) -> None:
        normalized = normalize_status(status)

        if (
            not force
            and normalized == self.last_status
        ):
            return

        if post(
            "/bluetooth/playback-status",
            {"status": normalized},
        ):
            self.last_status = normalized

            print(
                f"Wiedergabestatus: {normalized}",
                flush=True,
            )

    def _send_position(
        self,
        position_ms: int,
        *,
        force: bool = False,
    ) -> None:
        position_ms = max(0, int(position_ms))

        # Verhindert unnötige identische Aktualisierungen.
        if (
            not force
            and position_ms == self.last_position_ms
        ):
            return

        duration_ms = int(
            self.last_track.get("Duration", 0) or 0
        )

        payload: dict[str, Any] = {
            "elapsed": position_ms / 1000.0,
        }

        if duration_ms > 0:
            payload["duration"] = duration_ms / 1000.0

        if post("/bluetooth/progress", payload):
            self.last_position_ms = position_ms

    def _poll_position(self) -> bool:
        if (
            not self.player_path
            or self.player_properties is None
        ):
            self._find_player()
            return True

        try:
            position = self.player_properties.Get(
                MEDIA_PLAYER_INTERFACE,
                "Position",
            )

            self._send_position(int(position))

        except dbus.DBusException:
            self._detach_player()
            self._find_player()

        return True


def main() -> int:
    try:
        watcher = AvrcpWatcher()
        watcher.start()
        return 0

    except KeyboardInterrupt:
        return 0

    except Exception as error:
        print(
            f"Unerwarteter Fehler: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
