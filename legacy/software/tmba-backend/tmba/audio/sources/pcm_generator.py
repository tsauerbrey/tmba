"""Deterministic PCM signal generation for source and hardware tests."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class PcmFormat:
    """Raw PCM stream description used by generated test sources."""

    sample_rate: int = 48_000
    channels: int = 2
    sample_format: str = "S16_LE"

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero.")
        if self.channels not in {1, 2}:
            raise ValueError("channels must be 1 or 2.")
        if self.sample_format != "S16_LE":
            raise ValueError("The PCM generator currently supports S16_LE only.")

    @property
    def bytes_per_sample(self) -> int:
        return 2

    @property
    def frame_size(self) -> int:
        return self.channels * self.bytes_per_sample


class SineWaveGenerator:
    """Generate phase-continuous signed 16-bit little-endian sine PCM."""

    def __init__(
        self,
        *,
        frequency_hz: float = 440.0,
        amplitude: float = 0.20,
        pcm_format: PcmFormat | None = None,
    ) -> None:
        if frequency_hz <= 0:
            raise ValueError("frequency_hz must be greater than zero.")
        if not 0.0 <= amplitude <= 1.0:
            raise ValueError("amplitude must be between 0.0 and 1.0.")
        self.frequency_hz = float(frequency_hz)
        self.amplitude = float(amplitude)
        self.pcm_format = pcm_format or PcmFormat()
        self._phase = 0.0

    def reset(self) -> None:
        self._phase = 0.0

    def generate_frames(self, frame_count: int) -> bytes:
        if frame_count < 0:
            raise ValueError("frame_count must not be negative.")
        if frame_count == 0:
            return b""

        phase_step = 2.0 * math.pi * self.frequency_hz / self.pcm_format.sample_rate
        maximum = 32_767
        output = bytearray(frame_count * self.pcm_format.frame_size)
        offset = 0

        for _ in range(frame_count):
            value = int(round(math.sin(self._phase) * maximum * self.amplitude))
            packed = struct.pack("<h", value)
            for _channel in range(self.pcm_format.channels):
                output[offset : offset + 2] = packed
                offset += 2
            self._phase = (self._phase + phase_step) % (2.0 * math.pi)

        return bytes(output)

    def generate_duration(self, duration_seconds: float) -> bytes:
        if duration_seconds < 0:
            raise ValueError("duration_seconds must not be negative.")
        frames = round(duration_seconds * self.pcm_format.sample_rate)
        return self.generate_frames(frames)

    def blocks(self, frames_per_block: int) -> Iterator[bytes]:
        if frames_per_block <= 0:
            raise ValueError("frames_per_block must be greater than zero.")
        while True:
            yield self.generate_frames(frames_per_block)
