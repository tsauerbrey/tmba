"""ALSA output-driver foundation for TMBA."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Sequence

from tmba.audio.outputs.base import (
    OutputDriver,
    OutputState,
    OutputStatus,
)
from tmba.audio.pipeline_config import OutputConfig


CommandRunner = Callable[
    [Sequence[str]],
    subprocess.CompletedProcess[str],
]


@dataclass(frozen=True, slots=True)
class AlsaDevice:
    """A playback device reported by ``aplay -l``."""

    card_index: int
    card_id: str
    card_name: str
    device_index: int
    device_id: str
    device_name: str

    @property
    def hardware_address(self) -> str:
        return f"hw:{self.card_index},{self.device_index}"

    def to_dict(self) -> dict[str, object]:
        return {
            "card_index": self.card_index,
            "card_id": self.card_id,
            "card_name": self.card_name,
            "device_index": self.device_index,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "hardware_address": self.hardware_address,
        }


class AlsaOutputError(RuntimeError):
    """Raised when the ALSA environment cannot be prepared safely."""


class AlsaOutputDriver(OutputDriver):
    """
    ALSA output-driver foundation.

    v0.6.2-A performs environment and device discovery only. It deliberately
    does not stream audio samples or keep an ``aplay`` process open yet.
    """

    driver_name = "alsa"

    _CARD_PREFIX = re.compile(
        r"^card\s+(?P<card_index>\d+):\s*"
        r"(?P<card_id>[^\s]+)\s+\[(?P<card_name>[^\]]+)\],\s*"
        r"device\s+(?P<device_index>\d+):\s*"
        r"(?P<device_section>.+)$"
    )

    _TRAILING_BRACKETS = re.compile(
        r"^(?P<device_id>.+?)\s+\[(?P<device_name>[^\]]+)\]\s*$"
    )

    def __init__(
        self,
        config: OutputConfig,
        *,
        command_runner: CommandRunner | None = None,
        platform_name: str | None = None,
        executable_finder: Callable[[str], str | None] | None = None,
    ) -> None:
        self._config = config
        self._state = OutputState.STOPPED
        self._command_runner = command_runner or self._run_command
        self._platform_name = platform_name or sys.platform
        self._executable_finder = executable_finder or shutil.which
        self._devices: list[AlsaDevice] = []
        self._error: str | None = None
        self._aplay_path: str | None = None

    @staticmethod
    def _run_command(
        command: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

    @classmethod
    def parse_device_list(cls, output: str) -> list[AlsaDevice]:
        devices: list[AlsaDevice] = []

        for raw_line in output.splitlines():
            line = raw_line.strip()
            card_match = cls._CARD_PREFIX.match(line)
            if card_match is None:
                continue

            values = card_match.groupdict()
            device_section = values["device_section"].strip()
            device_match = cls._TRAILING_BRACKETS.match(
                device_section
            )
            if device_match is None:
                continue

            device_values = device_match.groupdict()

            devices.append(
                AlsaDevice(
                    card_index=int(values["card_index"]),
                    card_id=values["card_id"],
                    card_name=values["card_name"].strip(),
                    device_index=int(values["device_index"]),
                    device_id=device_values["device_id"].strip(),
                    device_name=device_values["device_name"].strip(),
                )
            )

        return devices

    def discover_devices(self) -> tuple[AlsaDevice, ...]:
        self._ensure_linux()

        aplay_path = self._executable_finder("aplay")
        if aplay_path is None:
            raise AlsaOutputError(
                "Das ALSA-Werkzeug 'aplay' wurde nicht gefunden."
            )

        result = self._command_runner([aplay_path, "-l"])
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            raise AlsaOutputError(
                "ALSA-Geräte konnten nicht ermittelt werden"
                + (f": {message}" if message else ".")
            )

        self._aplay_path = aplay_path
        self._devices = self.parse_device_list(result.stdout)
        return tuple(self._devices)

    def start(self) -> None:
        self._state = OutputState.STARTING
        self._error = None

        try:
            devices = self.discover_devices()
            self._validate_configured_device(devices)
        except Exception as error:
            self._state = OutputState.ERROR
            self._error = str(error)
            raise

        # v0.6.2-A validates and prepares ALSA only. Real PCM streaming follows
        # in the Raspberry-Pi hardware milestone.
        self._state = OutputState.READY

    def stop(self) -> None:
        self._state = OutputState.STOPPED
        self._error = None

    def status(self) -> OutputStatus:
        return OutputStatus(
            driver=self.driver_name,
            state=self._state,
            device=self._config.device,
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            format=self._config.format,
            details={
                "simulation": False,
                "platform": self._platform_name,
                "aplay_path": self._aplay_path,
                "device_count": len(self._devices),
                "devices": [
                    device.to_dict()
                    for device in self._devices
                ],
                "streaming": False,
                "error": self._error,
            },
        )

    def _ensure_linux(self) -> None:
        if not self._platform_name.startswith("linux"):
            raise AlsaOutputError(
                "ALSA-Ausgabe ist nur auf Linux verfügbar."
            )

    def _validate_configured_device(
        self,
        devices: tuple[AlsaDevice, ...],
    ) -> None:
        configured = self._config.device.strip()

        if configured in {"", "default"}:
            return

        available = {
            device.hardware_address
            for device in devices
        }

        if configured.startswith(("plughw:", "sysdefault:", "dmix:")):
            return

        if configured.startswith("hw:") and configured not in available:
            raise AlsaOutputError(
                f"Das konfigurierte ALSA-Gerät '{configured}' "
                "wurde nicht gefunden."
            )
