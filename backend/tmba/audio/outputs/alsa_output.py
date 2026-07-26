"""ALSA PCM output driver for TMBA."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from threading import RLock
from typing import BinaryIO, Callable, Protocol, Sequence

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


class PlaybackProcess(Protocol):
    """Minimal process contract needed by the ALSA driver."""

    stdin: BinaryIO | None
    stderr: BinaryIO | None

    def poll(self) -> int | None:
        ...

    def terminate(self) -> None:
        ...

    def kill(self) -> None:
        ...

    def wait(self, timeout: float | None = None) -> int:
        ...


ProcessFactory = Callable[[Sequence[str]], PlaybackProcess]


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
    """Raised when ALSA playback cannot be prepared or maintained."""


class AlsaOutputDriver(OutputDriver):
    """Stream raw PCM bytes to a persistent ``aplay`` process."""

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

    _SUPPORTED_FORMATS = {
        "S16_LE",
        "S24_3LE",
        "S24_LE",
        "S32_LE",
        "FLOAT_LE",
    }

    def __init__(
        self,
        config: OutputConfig,
        *,
        command_runner: CommandRunner | None = None,
        process_factory: ProcessFactory | None = None,
        platform_name: str | None = None,
        executable_finder: Callable[[str], str | None] | None = None,
    ) -> None:
        self._config = config
        self._state = OutputState.STOPPED
        self._command_runner = command_runner or self._run_command
        self._process_factory = process_factory or self._start_process
        self._platform_name = platform_name or sys.platform
        self._executable_finder = executable_finder or shutil.which
        self._devices: list[AlsaDevice] = []
        self._error: str | None = None
        self._aplay_path: str | None = None
        self._process: PlaybackProcess | None = None
        self._bytes_written = 0
        self._lock = RLock()

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

    @staticmethod
    def _start_process(command: Sequence[str]) -> PlaybackProcess:
        return subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
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
            device_match = cls._TRAILING_BRACKETS.match(
                values["device_section"].strip()
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
        aplay_path = self._find_aplay()

        result = self._command_runner([aplay_path, "-l"])
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            raise AlsaOutputError(
                "ALSA-Geräte konnten nicht ermittelt werden"
                + (f": {message}" if message else ".")
            )

        self._devices = self.parse_device_list(result.stdout)
        return tuple(self._devices)

    def build_playback_command(self) -> list[str]:
        """Return the exact ``aplay`` command for raw PCM playback."""

        aplay_path = self._find_aplay()
        audio_format = self._config.format.strip().upper()
        if audio_format not in self._SUPPORTED_FORMATS:
            raise AlsaOutputError(
                f"Das PCM-Format '{self._config.format}' wird nicht unterstützt."
            )

        device = self._config.device.strip() or "default"
        return [
            aplay_path,
            "--quiet",
            "--device",
            device,
            "--file-type",
            "raw",
            "--format",
            audio_format,
            "--rate",
            str(self._config.sample_rate),
            "--channels",
            str(self._config.channels),
        ]

    def start(self) -> None:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return

            self._state = OutputState.STARTING
            self._error = None
            self._bytes_written = 0

            try:
                devices = self.discover_devices()
                self._validate_configured_device(devices)
                command = self.build_playback_command()
                process = self._process_factory(command)

                if process.stdin is None:
                    raise AlsaOutputError(
                        "Der ALSA-Wiedergabeprozess besitzt keinen PCM-Eingang."
                    )

                exit_code = process.poll()
                if exit_code is not None:
                    raise AlsaOutputError(
                        "Der ALSA-Wiedergabeprozess wurde sofort beendet "
                        f"(Exit-Code {exit_code})."
                    )

                self._process = process
                self._state = OutputState.RUNNING
            except Exception as error:
                self._process = None
                self._state = OutputState.ERROR
                self._error = str(error)
                raise

    def write(self, pcm_data: bytes) -> int:
        """Write one raw PCM block to ALSA and return its byte count."""

        if not isinstance(pcm_data, bytes):
            raise TypeError("PCM-Daten müssen als bytes übergeben werden.")
        if not pcm_data:
            return 0

        with self._lock:
            process = self._process
            if process is None or self._state is not OutputState.RUNNING:
                raise AlsaOutputError(
                    "Die ALSA-Ausgabe wurde noch nicht gestartet."
                )

            exit_code = process.poll()
            if exit_code is not None:
                self._set_runtime_error(
                    "Der ALSA-Wiedergabeprozess ist beendet "
                    f"(Exit-Code {exit_code})."
                )

            if process.stdin is None:
                self._set_runtime_error(
                    "Der ALSA-Wiedergabeprozess besitzt keinen PCM-Eingang."
                )

            try:
                written = process.stdin.write(pcm_data)
                process.stdin.flush()
            except (BrokenPipeError, OSError) as error:
                self._set_runtime_error(
                    f"PCM-Daten konnten nicht an ALSA gesendet werden: {error}"
                )

            byte_count = len(pcm_data) if written is None else int(written)
            self._bytes_written += byte_count
            return byte_count

    def stop(self) -> None:
        with self._lock:
            process = self._process
            self._process = None

            if process is not None:
                if process.stdin is not None:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass

                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=2.0)

            self._state = OutputState.STOPPED
            self._error = None

    def status(self) -> OutputStatus:
        with self._lock:
            process_running = (
                self._process is not None
                and self._process.poll() is None
            )
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
                    "streaming": process_running,
                    "bytes_written": self._bytes_written,
                    "error": self._error,
                },
            )

    def _find_aplay(self) -> str:
        self._ensure_linux()
        aplay_path = self._executable_finder("aplay")
        if aplay_path is None:
            raise AlsaOutputError(
                "Das ALSA-Werkzeug 'aplay' wurde nicht gefunden."
            )
        self._aplay_path = aplay_path
        return aplay_path

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

        if configured.startswith(("plughw:", "sysdefault:", "dmix:")):
            return

        available = {
            device.hardware_address
            for device in devices
        }
        if configured.startswith("hw:") and configured not in available:
            raise AlsaOutputError(
                f"Das konfigurierte ALSA-Gerät '{configured}' "
                "wurde nicht gefunden."
            )

    def _set_runtime_error(self, message: str) -> None:
        self._state = OutputState.ERROR
        self._error = message
        raise AlsaOutputError(message)
