from __future__ import annotations

from dataclasses import asdict

import pytest

from tmba.audio.outputs.null_output import NullOutputDriver
from tmba.audio.pipeline import AudioPipeline, PipelineState
from tmba.audio.pipeline_config import OutputConfig, PipelineConfig
from tmba.audio.pipeline_stage import PipelineStage, StageState
from tmba.audio.stages import OutputStage


class DummyStage(PipelineStage):
    stage_type = "dummy"


def test_default_pipeline_has_expected_order() -> None:
    pipeline = AudioPipeline()

    assert [stage.stage_type for stage in pipeline.stages] == [
        "source_gain",
        "replay_gain",
        "loudness",
        "equalizer",
        "limiter",
        "output",
    ]
    assert [stage.order for stage in pipeline.stages] == list(range(6))


def test_pipeline_has_exactly_one_output_stage() -> None:
    pipeline = AudioPipeline()

    assert sum(stage.stage_type == "output" for stage in pipeline.stages) == 1
    assert pipeline.stages[-1].stage_type == "output"


def test_duplicate_stage_names_are_rejected() -> None:
    stages = [
        DummyStage("duplicate"),
        DummyStage("duplicate"),
        OutputStage(PipelineConfig()),
    ]

    with pytest.raises(ValueError, match="unique"):
        AudioPipeline(stages=stages)


def test_missing_output_stage_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly one output"):
        AudioPipeline(stages=[DummyStage("one")])


def test_output_stage_must_be_last() -> None:
    config = PipelineConfig()
    stages = [OutputStage(config), DummyStage("after-output")]

    with pytest.raises(ValueError, match="final"):
        AudioPipeline(config=config, stages=stages)


def test_stage_can_be_disabled_and_enabled() -> None:
    pipeline = AudioPipeline()

    pipeline.disable_stage("equalizer")
    assert pipeline.get_stage("equalizer").enabled is False
    assert pipeline.get_stage("equalizer").state is StageState.BYPASSED

    pipeline.enable_stage("equalizer")
    assert pipeline.get_stage("equalizer").enabled is True
    assert pipeline.get_stage("equalizer").state is StageState.READY


def test_output_stage_cannot_be_disabled() -> None:
    pipeline = AudioPipeline()

    with pytest.raises(ValueError, match="cannot be disabled"):
        pipeline.disable_stage("output")


def test_null_output_lifecycle() -> None:
    driver = NullOutputDriver(OutputConfig())

    assert driver.status().state.value == "stopped"
    driver.start()
    assert driver.status().state.value == "running"
    driver.stop()
    assert driver.status().state.value == "stopped"


def test_pipeline_start_and_stop() -> None:
    pipeline = AudioPipeline()

    pipeline.start()
    assert pipeline.state is PipelineState.RUNNING
    assert all(
        stage.state in {StageState.ACTIVE, StageState.BYPASSED}
        for stage in pipeline.stages
    )

    pipeline.stop()
    assert pipeline.state is PipelineState.STOPPED
    assert all(stage.state is StageState.CREATED for stage in pipeline.stages)


def test_pipeline_status_is_serializable_structure() -> None:
    pipeline = AudioPipeline()
    pipeline.start()

    status = asdict(pipeline.status())

    assert status["state"] is PipelineState.RUNNING
    assert status["stage_count"] == 6
    assert status["output"]["driver"] == "null"
    assert status["output"]["details"]["simulation"] is True
    assert len(status["stages"]) == 6


def test_invalid_output_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="driver"):
        OutputConfig(driver="unknown")


def test_unknown_stage_raises_key_error() -> None:
    pipeline = AudioPipeline()

    with pytest.raises(KeyError, match="Unknown pipeline stage"):
        pipeline.get_stage("not-present")
