from __future__ import annotations

from tmba.audio.pipeline_config import PipelineConfig
from tmba.audio.pipeline_stage import PipelineStage


class SourceGainStage(PipelineStage):
    stage_type = "source_gain"

    def __init__(self, config: PipelineConfig) -> None:
        super().__init__("source_gain", enabled=config.source_gain.enabled)
        self.set_detail("gain_db", config.source_gain.gain_db)


class ReplayGainStage(PipelineStage):
    stage_type = "replay_gain"

    def __init__(self, config: PipelineConfig) -> None:
        super().__init__("replay_gain", enabled=config.replay_gain.enabled)
        self.set_detail("preamp_db", config.replay_gain.preamp_db)
        self.set_detail("prevent_clipping", config.replay_gain.prevent_clipping)


class LoudnessStage(PipelineStage):
    stage_type = "loudness"

    def __init__(self, config: PipelineConfig) -> None:
        super().__init__("loudness", enabled=config.loudness.enabled)
        self.set_detail("reference_volume", config.loudness.reference_volume)


class EqualizerStage(PipelineStage):
    stage_type = "equalizer"

    def __init__(self, config: PipelineConfig) -> None:
        super().__init__("equalizer", enabled=config.equalizer.enabled)
        self.set_detail("preset", config.equalizer.preset)


class LimiterStage(PipelineStage):
    stage_type = "limiter"

    def __init__(self, config: PipelineConfig) -> None:
        super().__init__("limiter", enabled=config.limiter.enabled)
        self.set_detail("threshold_db", config.limiter.threshold_db)


class OutputStage(PipelineStage):
    stage_type = "output"

    def __init__(self, config: PipelineConfig) -> None:
        super().__init__("output", enabled=True)
        self.set_detail("driver", config.output.driver)
        self.set_detail("device", config.output.device)
        self.set_detail("gain_db", config.output.gain_db)
