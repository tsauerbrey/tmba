from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _validate_gain(value: float, field_name: str) -> float:
    numeric = float(value)
    if not -120.0 <= numeric <= 24.0:
        raise ValueError(f"{field_name} must be between -120.0 dB and 24.0 dB.")
    return numeric


@dataclass(slots=True)
class SourceGainConfig:
    enabled: bool = True
    gain_db: float = 0.0

    def __post_init__(self) -> None:
        self.gain_db = _validate_gain(self.gain_db, "source gain")


@dataclass(slots=True)
class ReplayGainConfig:
    enabled: bool = False
    preamp_db: float = 0.0
    prevent_clipping: bool = True

    def __post_init__(self) -> None:
        self.preamp_db = _validate_gain(self.preamp_db, "ReplayGain preamp")


@dataclass(slots=True)
class LoudnessConfig:
    enabled: bool = False
    reference_volume: int = 50

    def __post_init__(self) -> None:
        if not 0 <= int(self.reference_volume) <= 100:
            raise ValueError("Loudness reference volume must be between 0 and 100.")
        self.reference_volume = int(self.reference_volume)


@dataclass(slots=True)
class EqualizerConfig:
    enabled: bool = False
    preset: str = "flat"


@dataclass(slots=True)
class LimiterConfig:
    enabled: bool = True
    threshold_db: float = -1.0

    def __post_init__(self) -> None:
        if not -30.0 <= float(self.threshold_db) <= 0.0:
            raise ValueError("Limiter threshold must be between -30.0 dB and 0.0 dB.")
        self.threshold_db = float(self.threshold_db)


@dataclass(slots=True)
class OutputConfig:
    driver: str = "null"
    device: str = "simulation"
    sample_rate: int = 48_000
    channels: int = 2
    format: str = "S32_LE"
    gain_db: float = 0.0

    def __post_init__(self) -> None:
        if self.driver not in {"null", "alsa"}:
            raise ValueError("Output driver must be 'null' or 'alsa'.")
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be greater than zero.")
        if self.channels not in {1, 2}:
            raise ValueError("Channels must be 1 or 2.")
        self.gain_db = _validate_gain(self.gain_db, "output gain")


@dataclass(slots=True)
class PipelineConfig:
    source_gain: SourceGainConfig = field(default_factory=SourceGainConfig)
    replay_gain: ReplayGainConfig = field(default_factory=ReplayGainConfig)
    loudness: LoudnessConfig = field(default_factory=LoudnessConfig)
    equalizer: EqualizerConfig = field(default_factory=EqualizerConfig)
    limiter: LimiterConfig = field(default_factory=LimiterConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


    @classmethod
    def from_settings(cls) -> "PipelineConfig":
        """Build the runtime pipeline from the repository audio.yaml file."""
        from tmba.core.config import get_settings

        settings = get_settings().audio
        hardware = settings.hardware
        return cls(
            output=OutputConfig(
                driver="alsa",
                device=str(hardware.alsa_device),
                sample_rate=int(hardware.sample_rate),
                channels=int(hardware.channels),
                format=str(hardware.sample_format),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
