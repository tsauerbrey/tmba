from tmba.audio.outputs.alsa_output import AlsaOutputDriver
from tmba.audio.outputs.factory import create_output_driver
from tmba.audio.outputs.null_output import NullOutputDriver
from tmba.audio.pipeline import AudioPipeline
from tmba.audio.pipeline_config import (
    OutputConfig,
    PipelineConfig,
)


def test_factory_creates_null_output() -> None:
    driver = create_output_driver(
        OutputConfig()
    )

    assert isinstance(driver, NullOutputDriver)


def test_factory_creates_alsa_output() -> None:
    driver = create_output_driver(
        OutputConfig(
            driver="alsa",
            device="default",
        )
    )

    assert isinstance(driver, AlsaOutputDriver)


def test_pipeline_uses_configured_factory_driver() -> None:
    pipeline = AudioPipeline(
        config=PipelineConfig(
            output=OutputConfig(
                driver="alsa",
                device="default",
            )
        )
    )

    assert isinstance(
        pipeline.output_driver,
        AlsaOutputDriver,
    )
    assert (
        pipeline.status().output["driver"]
        == "alsa"
    )


def test_injected_driver_still_takes_precedence() -> None:
    injected = NullOutputDriver()
    pipeline = AudioPipeline(
        config=PipelineConfig(
            output=OutputConfig(
                driver="alsa",
                device="default",
            )
        ),
        output_driver=injected,
    )

    assert pipeline.output_driver is injected
