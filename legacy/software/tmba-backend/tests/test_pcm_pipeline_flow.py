from __future__ import annotations

from tmba.audio.outputs.null_output import NullOutputDriver
from tmba.audio.pipeline import AudioPipeline
from tmba.audio.pipeline_config import OutputConfig, PipelineConfig
from tmba.audio.sources import DummySource


def test_pipeline_forwards_pcm_to_output_driver():
    driver = NullOutputDriver(OutputConfig(driver="null", device="simulation"))
    pipeline = AudioPipeline(output_driver=driver)
    pipeline.start()

    assert pipeline.write(b"\x00\x01\x02\x03") == 4
    assert driver.status().details["bytes_written"] == 4
    pipeline.stop()


def test_dummy_source_can_feed_running_pipeline():
    driver = NullOutputDriver(OutputConfig(driver="null", device="simulation"))
    pipeline = AudioPipeline(
        config=PipelineConfig(output=OutputConfig(driver="null")),
        output_driver=driver,
    )
    pipeline.start()
    source = DummySource(pipeline.write, frames_per_block=48)
    source.start()

    import time
    deadline = time.monotonic() + 1.0
    while driver.status().details["bytes_written"] == 0 and time.monotonic() < deadline:
        time.sleep(0.005)

    source.stop()
    pipeline.stop()
    assert driver.status().details["bytes_written"] > 0
