"""Hardware test-tone playback for TMBA."""

from __future__ import annotations

from dataclasses import dataclass

from tmba.audio.outputs.alsa_output import AlsaOutputDriver
from tmba.audio.pipeline_config import OutputConfig, PipelineConfig
from tmba.audio.sources.pcm_generator import PcmFormat, SineWaveGenerator


@dataclass(frozen=True, slots=True)
class TestToneResult:
    frequency_hz: float
    duration_seconds: float
    amplitude: float
    bytes_written: int
    output: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "success": True,
            "frequency_hz": self.frequency_hz,
            "duration_seconds": self.duration_seconds,
            "amplitude": self.amplitude,
            "bytes_written": self.bytes_written,
            "output": self.output,
        }


def play_test_tone(
    *,
    frequency_hz: float = 440.0,
    duration_seconds: float = 3.0,
    amplitude: float = 0.20,
) -> TestToneResult:
    """Play a short stereo sine wave through the configured ALSA device."""

    runtime = PipelineConfig.from_settings().output
    output_config = OutputConfig(
        driver="alsa",
        device=runtime.device,
        sample_rate=runtime.sample_rate,
        channels=runtime.channels,
        format="S16_LE",
    )
    pcm_format = PcmFormat(
        sample_rate=output_config.sample_rate,
        channels=output_config.channels,
        sample_format="S16_LE",
    )
    generator = SineWaveGenerator(
        frequency_hz=frequency_hz,
        amplitude=amplitude,
        pcm_format=pcm_format,
    )
    driver = AlsaOutputDriver(output_config)

    try:
        driver.start()
        bytes_written = 0
        remaining_frames = round(duration_seconds * pcm_format.sample_rate)
        frames_per_block = 2048
        while remaining_frames > 0:
            frame_count = min(frames_per_block, remaining_frames)
            bytes_written += driver.write(generator.generate_frames(frame_count))
            remaining_frames -= frame_count
        status = driver.status()
        output = {
            "driver": status.driver,
            "device": status.device,
            "sample_rate": status.sample_rate,
            "channels": status.channels,
            "format": status.format,
            "details": status.details,
        }
    finally:
        driver.stop()

    return TestToneResult(
        frequency_hz=frequency_hz,
        duration_seconds=duration_seconds,
        amplitude=amplitude,
        bytes_written=bytes_written,
        output=output,
    )
