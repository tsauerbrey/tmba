from __future__ import annotations

import struct

import pytest

from tmba.audio.sources import PcmFormat, SineWaveGenerator


def test_pcm_format_reports_frame_size():
    pcm_format = PcmFormat(sample_rate=48_000, channels=2)
    assert pcm_format.bytes_per_sample == 2
    assert pcm_format.frame_size == 4


def test_generator_returns_expected_stereo_byte_count():
    generator = SineWaveGenerator(
        frequency_hz=440.0,
        amplitude=0.25,
        pcm_format=PcmFormat(sample_rate=48_000, channels=2),
    )
    block = generator.generate_frames(960)
    assert len(block) == 960 * 2 * 2


def test_generator_duplicates_each_sample_to_both_channels():
    generator = SineWaveGenerator(
        frequency_hz=1_000.0,
        amplitude=0.5,
        pcm_format=PcmFormat(sample_rate=48_000, channels=2),
    )
    block = generator.generate_frames(8)
    samples = struct.unpack("<16h", block)
    assert all(samples[index] == samples[index + 1] for index in range(0, 16, 2))
    assert any(value != 0 for value in samples[2:])


def test_generator_is_phase_continuous_across_blocks():
    first = SineWaveGenerator(frequency_hz=440.0)
    split = first.generate_frames(100) + first.generate_frames(100)
    second = SineWaveGenerator(frequency_hz=440.0)
    whole = second.generate_frames(200)
    assert split == whole


def test_reset_restarts_wave_at_zero_phase():
    generator = SineWaveGenerator(frequency_hz=440.0)
    original = generator.generate_frames(20)
    generator.generate_frames(100)
    generator.reset()
    assert generator.generate_frames(20) == original


def test_duration_generation_rounds_to_sample_frames():
    generator = SineWaveGenerator(
        pcm_format=PcmFormat(sample_rate=48_000, channels=1)
    )
    assert len(generator.generate_duration(0.01)) == 480 * 2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"frequency_hz": 0}, "frequency_hz"),
        ({"amplitude": 1.1}, "amplitude"),
    ],
)
def test_generator_rejects_invalid_settings(kwargs, message):
    with pytest.raises(ValueError, match=message):
        SineWaveGenerator(**kwargs)
