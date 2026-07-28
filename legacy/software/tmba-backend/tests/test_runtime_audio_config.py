from tmba.audio.pipeline_config import PipelineConfig


def test_runtime_audio_config_uses_named_hifiberry_device() -> None:
    config = PipelineConfig.from_settings()
    assert config.output.driver == "alsa"
    assert config.output.device == "hw:CARD=sndrpihifiberry,DEV=0"
    assert config.output.sample_rate == 48_000
    assert config.output.channels == 2
    assert config.output.format == "S16_LE"
