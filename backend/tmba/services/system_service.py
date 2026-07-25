"""System information and diagnostics service for TMBA."""

from __future__ import annotations

import platform
import shutil
import socket
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

from tmba.core.config import get_settings


@dataclass(frozen=True)
class MemoryInfo:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    percent: float


@dataclass(frozen=True)
class DiskInfo:
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


@dataclass(frozen=True)
class CpuInfo:
    logical_cores: int
    physical_cores: int | None
    usage_percent: float
    temperature_celsius: float | None


class SystemService:
    """Collect platform-independent TMBA system information."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._process_started_monotonic = time.monotonic()
        self._process_started_at = datetime.now(timezone.utc)

    def get_info(self) -> dict[str, Any]:
        memory = psutil.virtual_memory()
        disk_path = self._resolve_disk_path()
        disk = shutil.disk_usage(disk_path)

        total_disk = disk.total
        used_disk = disk.used
        disk_percent = (
            round((used_disk / total_disk) * 100, 1)
            if total_disk > 0
            else 0.0
        )

        boot_timestamp = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_timestamp, tz=timezone.utc)

        memory_info = MemoryInfo(
            total_bytes=int(memory.total),
            available_bytes=int(memory.available),
            used_bytes=int(memory.used),
            percent=float(memory.percent),
        )

        disk_info = DiskInfo(
            path=str(disk_path),
            total_bytes=int(total_disk),
            used_bytes=int(used_disk),
            free_bytes=int(disk.free),
            percent=disk_percent,
        )

        cpu_info = CpuInfo(
            logical_cores=psutil.cpu_count(logical=True) or 1,
            physical_cores=psutil.cpu_count(logical=False),
            usage_percent=float(psutil.cpu_percent(interval=0.1)),
            temperature_celsius=self._get_cpu_temperature(),
        )

        return {
            "project": self._settings.system.project.name,
            "full_name": self._settings.system.project.full_name,
            "version": self._settings.system.project.version,
            "environment": self._settings.system.project.environment,
            "hostname": socket.gethostname(),
            "configured_hostname": self._settings.system.device.hostname,
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor() or None,
                "python": platform.python_version(),
            },
            "network": {
                "local_ip": self._get_local_ip(),
            },
            "uptime": {
                "system_seconds": max(0, int(time.time() - boot_timestamp)),
                "system_started_at": boot_time.isoformat(),
                "backend_seconds": max(
                    0,
                    int(time.monotonic() - self._process_started_monotonic),
                ),
                "backend_started_at": self._process_started_at.isoformat(),
            },
            "cpu": asdict(cpu_info),
            "memory": asdict(memory_info),
            "disk": asdict(disk_info),
            "dsp": {
                "configured": bool(self._settings.dsp.enabled),
                "engine": self._settings.dsp.engine,
                "active_preset": self._settings.dsp.active_preset,
            },
            "display": {
                "width": self._settings.display.display.width,
                "height": self._settings.display.display.height,
                "rotation": self._settings.display.display.rotation,
                "kiosk_enabled": self._settings.display.kiosk.enabled,
            },
            "webui": {
                "enabled": self._settings.network.webui.enabled,
                "port": self._settings.network.webui.port,
                "local_hostname": self._settings.network.webui.local_hostname,
            },
        }

    def get_health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "project": self._settings.system.project.name,
            "version": self._settings.system.project.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _resolve_disk_path(self) -> Path:
        config_directory = self._settings.config_directory
        project_directory = config_directory.parent
        return project_directory if project_directory.exists() else Path("/")

    @staticmethod
    def _get_local_ip() -> str | None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return None
        finally:
            sock.close()

    @staticmethod
    def _get_cpu_temperature() -> float | None:
        try:
            temperatures = psutil.sensors_temperatures(fahrenheit=False)
        except (AttributeError, OSError):
            return None

        preferred_groups = (
            "cpu_thermal",
            "coretemp",
            "apple_smc",
            "acpitz",
        )

        for group_name in preferred_groups:
            entries = temperatures.get(group_name, [])
            for entry in entries:
                current = getattr(entry, "current", None)
                if isinstance(current, (int, float)):
                    return round(float(current), 1)

        for entries in temperatures.values():
            for entry in entries:
                current = getattr(entry, "current", None)
                if isinstance(current, (int, float)):
                    return round(float(current), 1)

        return None


system_service = SystemService()
