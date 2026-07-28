"""Network diagnostics and Wi-Fi management service for TMBA."""

from __future__ import annotations

import ipaddress
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from typing import Any

import psutil


@dataclass(frozen=True)
class InterfaceAddress:
    family: str
    address: str
    netmask: str | None
    broadcast: str | None


@dataclass(frozen=True)
class NetworkInterface:
    name: str
    is_up: bool
    speed_mbps: int | None
    mtu: int | None
    addresses: list[InterfaceAddress]


class NetworkService:
    """Provide portable network diagnostics and NetworkManager control."""

    def get_status(self) -> dict[str, Any]:
        interfaces = self._collect_interfaces()
        active_interfaces = [
            item
            for item in interfaces
            if item.is_up and self._has_usable_ip(item)
        ]

        local_ip = self._get_local_ip()

        return {
            "connected": local_ip is not None or bool(active_interfaces),
            "local_ip": local_ip,
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "backend": self._detect_backend(),
            "active_interfaces": [
                item.name for item in active_interfaces
            ],
            "wifi": self._get_wifi_connection(),
        }

    def get_interfaces(self) -> dict[str, Any]:
        interfaces = self._collect_interfaces()

        return {
            "count": len(interfaces),
            "interfaces": [
                {
                    "name": item.name,
                    "is_up": item.is_up,
                    "speed_mbps": item.speed_mbps,
                    "mtu": item.mtu,
                    "addresses": [
                        asdict(address)
                        for address in item.addresses
                    ],
                }
                for item in interfaces
            ],
        }

    def scan_wifi(self) -> dict[str, Any]:
        backend = self._detect_backend()

        if backend == "networkmanager":
            return self._scan_wifi_nmcli()

        if backend == "macos":
            return self._scan_wifi_macos()

        return self._unsupported(
            backend,
            "Auf diesem System ist kein unterstütztes "
            "WLAN-Scan-Werkzeug verfügbar.",
            networks=[],
        )

    def get_saved_wifi(self) -> dict[str, Any]:
        backend = self._detect_backend()

        if backend != "networkmanager":
            return self._unsupported(
                backend,
                "Gespeicherte WLAN-Verbindungen können nur über "
                "NetworkManager verwaltet werden.",
                connections=[],
            )

        result = self._run(
            [
                "nmcli",
                "-t",
                "--escape",
                "yes",
                "-f",
                "NAME,UUID,TYPE,DEVICE,AUTOCONNECT",
                "connection",
                "show",
            ]
        )

        if result.returncode != 0:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "connections": [],
                "error": self._command_error(result),
            }

        connections: list[dict[str, Any]] = []

        for line in result.stdout.splitlines():
            fields = self._split_nmcli_line(line)
            if len(fields) < 5:
                continue

            name, uuid, connection_type, device, autoconnect = fields[:5]
            if connection_type not in {
                "802-11-wireless",
                "wifi",
                "wireless",
            }:
                continue

            connections.append(
                {
                    "name": name,
                    "uuid": uuid,
                    "device": device or None,
                    "active": bool(device),
                    "autoconnect": autoconnect.lower() == "yes",
                }
            )

        connections.sort(
            key=lambda item: (
                not item["active"],
                item["name"].lower(),
            )
        )

        return {
            "supported": True,
            "backend": backend,
            "success": True,
            "connections": connections,
        }

    def connect_wifi(
        self,
        ssid: str,
        password: str | None = None,
        hidden: bool = False,
    ) -> dict[str, Any]:
        backend = self._detect_backend()

        if backend != "networkmanager":
            return self._unsupported(
                backend,
                "WLAN-Verbindungen können nur auf dem "
                "Raspberry Pi mit NetworkManager hergestellt werden.",
                success=False,
                ssid=ssid,
            )

        clean_ssid = ssid.strip()
        if not clean_ssid:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "ssid": clean_ssid,
                "error": "Die SSID darf nicht leer sein.",
            }

        existing = self._find_saved_connection(clean_ssid)

        if existing and not password:
            command = [
                "nmcli",
                "connection",
                "up",
                "uuid",
                existing["uuid"],
            ]
        else:
            command = [
                "nmcli",
                "device",
                "wifi",
                "connect",
                clean_ssid,
            ]

            if password:
                command.extend(["password", password])

            if hidden:
                command.extend(["hidden", "yes"])

        result = self._run(command, timeout=45)

        if result.returncode != 0:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "ssid": clean_ssid,
                "error": self._command_error(result),
            }

        status = self._get_wifi_connection_nmcli()

        return {
            "supported": True,
            "backend": backend,
            "success": True,
            "ssid": clean_ssid,
            "message": result.stdout.strip() or "WLAN verbunden.",
            "wifi": status,
        }

    def disconnect_wifi(
        self,
        interface: str | None = None,
    ) -> dict[str, Any]:
        backend = self._detect_backend()

        if backend != "networkmanager":
            return self._unsupported(
                backend,
                "WLAN-Verbindungen können nur auf dem "
                "Raspberry Pi mit NetworkManager getrennt werden.",
                success=False,
            )

        device = interface or self._find_wifi_device()
        if not device:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "error": "Es wurde keine WLAN-Schnittstelle gefunden.",
            }

        result = self._run(
            ["nmcli", "device", "disconnect", device],
            timeout=20,
        )

        if result.returncode != 0:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "interface": device,
                "error": self._command_error(result),
            }

        return {
            "supported": True,
            "backend": backend,
            "success": True,
            "interface": device,
            "message": result.stdout.strip() or "WLAN getrennt.",
        }

    def forget_wifi(
        self,
        connection: str,
    ) -> dict[str, Any]:
        backend = self._detect_backend()

        if backend != "networkmanager":
            return self._unsupported(
                backend,
                "Gespeicherte WLAN-Verbindungen können nur über "
                "NetworkManager gelöscht werden.",
                success=False,
                connection=connection,
            )

        clean_connection = connection.strip()
        if not clean_connection:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "error": "Der Verbindungsname darf nicht leer sein.",
            }

        result = self._run(
            [
                "nmcli",
                "connection",
                "delete",
                "id",
                clean_connection,
            ],
            timeout=20,
        )

        if result.returncode != 0:
            return {
                "supported": True,
                "backend": backend,
                "success": False,
                "connection": clean_connection,
                "error": self._command_error(result),
            }

        return {
            "supported": True,
            "backend": backend,
            "success": True,
            "connection": clean_connection,
            "message": (
                result.stdout.strip()
                or "Gespeicherte WLAN-Verbindung gelöscht."
            ),
        }

    def _collect_interfaces(self) -> list[NetworkInterface]:
        addresses_by_name = psutil.net_if_addrs()
        stats_by_name = psutil.net_if_stats()
        interfaces: list[NetworkInterface] = []

        for name in sorted(addresses_by_name):
            addresses: list[InterfaceAddress] = []

            for entry in addresses_by_name[name]:
                family_name = self._family_name(entry.family)
                if family_name not in {"IPv4", "IPv6", "MAC"}:
                    continue

                addresses.append(
                    InterfaceAddress(
                        family=family_name,
                        address=str(entry.address),
                        netmask=(
                            str(entry.netmask)
                            if entry.netmask
                            else None
                        ),
                        broadcast=(
                            str(entry.broadcast)
                            if entry.broadcast
                            else None
                        ),
                    )
                )

            stats = stats_by_name.get(name)
            interfaces.append(
                NetworkInterface(
                    name=name,
                    is_up=bool(stats.isup) if stats else False,
                    speed_mbps=(
                        int(stats.speed)
                        if stats and stats.speed >= 0
                        else None
                    ),
                    mtu=int(stats.mtu) if stats else None,
                    addresses=addresses,
                )
            )

        return interfaces

    @staticmethod
    def _family_name(family: Any) -> str:
        if family == socket.AF_INET:
            return "IPv4"
        if family == socket.AF_INET6:
            return "IPv6"

        family_text = str(family)
        if "AF_LINK" in family_text or "AF_PACKET" in family_text:
            return "MAC"

        return family_text

    @staticmethod
    def _has_usable_ip(interface: NetworkInterface) -> bool:
        for address in interface.addresses:
            if address.family != "IPv4":
                continue

            try:
                ip = ipaddress.ip_address(address.address)
            except ValueError:
                continue

            if not ip.is_loopback and not ip.is_unspecified:
                return True

        return False

    @staticmethod
    def _get_local_ip() -> str | None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
        except OSError:
            try:
                resolved = socket.gethostbyname(socket.gethostname())
                ip = ipaddress.ip_address(resolved)
                return None if ip.is_loopback else resolved
            except (OSError, ValueError):
                return None
        finally:
            sock.close()

    @staticmethod
    def _detect_backend() -> str:
        if shutil.which("nmcli"):
            return "networkmanager"

        if platform.system() == "Darwin":
            return "macos"

        return "generic"

    def _get_wifi_connection(self) -> dict[str, Any]:
        backend = self._detect_backend()

        if backend == "networkmanager":
            return self._get_wifi_connection_nmcli()

        if backend == "macos":
            return self._get_wifi_connection_macos()

        return {
            "supported": False,
            "connected": None,
            "ssid": None,
            "interface": None,
        }

    def _get_wifi_connection_nmcli(self) -> dict[str, Any]:
        result = self._run(
            [
                "nmcli",
                "-t",
                "--escape",
                "yes",
                "-f",
                "DEVICE,TYPE,STATE,CONNECTION",
                "device",
                "status",
            ]
        )

        if result.returncode != 0:
            return {
                "supported": True,
                "connected": None,
                "ssid": None,
                "interface": None,
                "error": self._command_error(result),
            }

        for line in result.stdout.splitlines():
            fields = self._split_nmcli_line(line)
            if len(fields) < 4:
                continue

            device, device_type, state, connection = fields[:4]
            if device_type == "wifi" and state == "connected":
                return {
                    "supported": True,
                    "connected": True,
                    "ssid": connection or None,
                    "interface": device or None,
                }

        return {
            "supported": True,
            "connected": False,
            "ssid": None,
            "interface": self._find_wifi_device(),
        }

    def _scan_wifi_nmcli(self) -> dict[str, Any]:
        result = self._run(
            [
                "nmcli",
                "-t",
                "--escape",
                "yes",
                "-f",
                "IN-USE,SSID,SIGNAL,SECURITY,FREQ",
                "device",
                "wifi",
                "list",
                "--rescan",
                "yes",
            ],
            timeout=25,
        )

        if result.returncode != 0:
            return {
                "supported": True,
                "backend": "networkmanager",
                "success": False,
                "networks": [],
                "error": self._command_error(result),
            }

        networks_by_key: dict[tuple[str, str], dict[str, Any]] = {}

        for line in result.stdout.splitlines():
            fields = self._split_nmcli_line(line)
            if len(fields) < 5:
                continue

            in_use, ssid, signal, security, frequency = fields[:5]
            ssid = ssid.strip()
            if not ssid:
                continue

            item = {
                "ssid": ssid,
                "signal_percent": self._to_int(signal),
                "security": security or "offen",
                "frequency_mhz": self._to_int(frequency),
                "connected": in_use.strip() == "*",
            }

            key = (ssid, item["security"])
            previous = networks_by_key.get(key)
            if (
                previous is None
                or (item["signal_percent"] or 0)
                > (previous["signal_percent"] or 0)
            ):
                networks_by_key[key] = item

        networks = sorted(
            networks_by_key.values(),
            key=lambda item: (
                not item["connected"],
                -(item["signal_percent"] or 0),
                item["ssid"].lower(),
            ),
        )

        return {
            "supported": True,
            "backend": "networkmanager",
            "success": True,
            "networks": networks,
        }

    def _get_wifi_connection_macos(self) -> dict[str, Any]:
        networksetup = shutil.which("networksetup")
        if not networksetup:
            return {
                "supported": False,
                "connected": None,
                "ssid": None,
                "interface": None,
            }

        interface = self._find_macos_wifi_interface(networksetup)
        if not interface:
            return {
                "supported": True,
                "connected": False,
                "ssid": None,
                "interface": None,
            }

        result = self._run(
            [networksetup, "-getairportnetwork", interface]
        )

        output = result.stdout.strip()
        if result.returncode == 0 and ":" in output:
            ssid = output.split(":", 1)[1].strip()
            if ssid and "not associated" not in ssid.lower():
                return {
                    "supported": True,
                    "connected": True,
                    "ssid": ssid,
                    "interface": interface,
                }

        return {
            "supported": True,
            "connected": False,
            "ssid": None,
            "interface": interface,
        }

    def _scan_wifi_macos(self) -> dict[str, Any]:
        candidates = [
            (
                "/System/Library/PrivateFrameworks/"
                "Apple80211.framework/Versions/Current/"
                "Resources/airport"
            ),
            "/usr/local/bin/airport",
            "/opt/homebrew/bin/airport",
        ]

        airport = next(
            (
                candidate
                for candidate in candidates
                if os.path.isfile(candidate)
                and os.access(candidate, os.X_OK)
            ),
            None,
        )

        if not airport:
            return self._unsupported(
                "macos",
                "macOS stellt auf diesem System kein nutzbares "
                "Kommandozeilenwerkzeug für WLAN-Scans bereit. "
                "Die Raspberry-Pi-Version verwendet NetworkManager.",
                networks=[],
            )

        result = self._run([airport, "-s"], timeout=20)
        if result.returncode != 0:
            return self._unsupported(
                "macos",
                self._command_error(result),
                networks=[],
            )

        networks: list[dict[str, Any]] = []
        lines = result.stdout.splitlines()

        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 7:
                continue

            try:
                bssid_index = next(
                    index
                    for index, part in enumerate(parts)
                    if part.count(":") == 5
                )
            except StopIteration:
                continue

            ssid = " ".join(parts[:bssid_index]).strip()
            if not ssid:
                continue

            networks.append(
                {
                    "ssid": ssid,
                    "signal_dbm": self._to_int(
                        parts[bssid_index + 1]
                    ),
                    "channel": parts[bssid_index + 2],
                    "security": (
                        " ".join(parts[bssid_index + 6:])
                        or "offen"
                    ),
                    "connected": False,
                }
            )

        return {
            "supported": True,
            "backend": "macos",
            "success": True,
            "networks": networks,
        }

    def _find_macos_wifi_interface(
        self,
        networksetup: str,
    ) -> str | None:
        result = self._run(
            [networksetup, "-listallhardwareports"]
        )

        lines = result.stdout.splitlines()
        for index, line in enumerate(lines):
            if line.strip() != "Hardware Port: Wi-Fi":
                continue

            if index + 1 >= len(lines):
                return None

            next_line = lines[index + 1].strip()
            if next_line.startswith("Device:"):
                return next_line.split(":", 1)[1].strip() or None

        return None

    def _find_wifi_device(self) -> str | None:
        result = self._run(
            [
                "nmcli",
                "-t",
                "--escape",
                "yes",
                "-f",
                "DEVICE,TYPE",
                "device",
                "status",
            ]
        )

        if result.returncode != 0:
            return None

        for line in result.stdout.splitlines():
            fields = self._split_nmcli_line(line)
            if len(fields) >= 2 and fields[1] == "wifi":
                return fields[0] or None

        return None

    def _find_saved_connection(
        self,
        name: str,
    ) -> dict[str, str] | None:
        saved = self.get_saved_wifi()
        if not saved.get("success"):
            return None

        for item in saved.get("connections", []):
            if item["name"] == name:
                return {
                    "name": item["name"],
                    "uuid": item["uuid"],
                }

        return None

    @staticmethod
    def _split_nmcli_line(line: str) -> list[str]:
        fields: list[str] = []
        current: list[str] = []
        escaped = False

        for char in line:
            if escaped:
                current.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == ":":
                fields.append("".join(current))
                current = []
            else:
                current.append(char)

        fields.append("".join(current))
        return fields

    @staticmethod
    def _to_int(value: str) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _command_error(
        result: subprocess.CompletedProcess[str],
    ) -> str:
        return (
            result.stderr.strip()
            or result.stdout.strip()
            or "Der Netzwerkbefehl ist fehlgeschlagen."
        )

    @staticmethod
    def _unsupported(
        backend: str,
        message: str,
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "supported": False,
            "backend": backend,
            "message": message,
            **extra,
        }

    @staticmethod
    def _run(
        command: list[str],
        timeout: int = 10,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return subprocess.CompletedProcess(
                command,
                returncode=1,
                stdout="",
                stderr=str(exc),
            )


network_service = NetworkService()
