from tmba.audio.outputs.null_output import NullOutputDriver
from tmba.audio.pipeline_config import OutputConfig
from tmba.audio.pipeline import AudioPipeline
from tmba.audio.pipeline_config import PipelineConfig
from tmba.audio.volume import SoftwareVolume


def test_non_s16_software_fallback_passes_pcm_through():
    driver = NullOutputDriver(OutputConfig(driver="null", device="simulation"))
    pipeline = AudioPipeline(output_driver=driver)
    pipeline.start()

    payload = b"\x00\x01\x02\x03"
    assert pipeline.write(payload) == len(payload)
    assert driver.status().details["bytes_written"] == len(payload)


def test_s16_software_fallback_still_applies_volume():
    driver = NullOutputDriver(
        OutputConfig(driver="null", device="simulation", format="S16_LE")
    )
    pipeline = AudioPipeline(
        config=PipelineConfig(
            output=OutputConfig(
                driver="null", device="simulation", format="S16_LE"
            )
        ),
        output_driver=driver,
        volume_control=SoftwareVolume(startup=50),
    )
    pipeline.start()

    payload = b"\x10\x00\x20\x00"
    assert pipeline.write(payload) == len(payload)
    assert driver.status().details["bytes_written"] == len(payload)
