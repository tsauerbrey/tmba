from __future__ import annotations

from tmba.audio.outputs.base import OutputDriver, OutputState, OutputStatus
from tmba.audio.pipeline_config import OutputConfig


class NullOutputDriver(OutputDriver):
    """
    Safe simulation output.

    It models lifecycle and configuration without opening an audio device.
    This is the default output for macOS development and automated tests.
    """

    driver_name = "null"

    def __init__(self, config: OutputConfig | None = None) -> None:
        self._config = config or OutputConfig()
        self._state = OutputState.STOPPED
        self._details: dict[str, object] = {
            "simulation": True,
            "bytes_written": 0,
        }

    def start(self) -> None:
        self._state = OutputState.STARTING
        self._state = OutputState.RUNNING

    def write(self, pcm_data: bytes) -> int:
        if not isinstance(pcm_data, bytes):
            raise TypeError("PCM-Daten müssen als bytes übergeben werden.")
        if self._state is not OutputState.RUNNING:
            raise RuntimeError("Die Null-Ausgabe wurde noch nicht gestartet.")
        byte_count = len(pcm_data)
        self._details["bytes_written"] = int(
            self._details.get("bytes_written", 0)
        ) + byte_count
        return byte_count

    def stop(self) -> None:
        self._state = OutputState.STOPPED

    def status(self) -> OutputStatus:
        return OutputStatus(
            driver=self.driver_name,
            state=self._state,
            device=self._config.device,
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            format=self._config.format,
            details=dict(self._details),
        )
