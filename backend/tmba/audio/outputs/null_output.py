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
        self._details: dict[str, object] = {"simulation": True}

    def start(self) -> None:
        self._state = OutputState.STARTING
        self._state = OutputState.RUNNING

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
