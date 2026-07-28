"""OutputDriver construction for the TMBA AudioPipeline."""

from __future__ import annotations

from tmba.audio.outputs.alsa_output import AlsaOutputDriver
from tmba.audio.outputs.base import OutputDriver
from tmba.audio.outputs.null_output import NullOutputDriver
from tmba.audio.pipeline_config import OutputConfig


def create_output_driver(config: OutputConfig) -> OutputDriver:
    """Create the configured output driver."""

    if config.driver == "null":
        return NullOutputDriver(config)

    if config.driver == "alsa":
        return AlsaOutputDriver(config)

    raise ValueError(
        f"Unbekannter OutputDriver: {config.driver}"
    )
