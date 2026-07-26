from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable

from tmba.audio.outputs.base import OutputDriver
from tmba.audio.outputs.factory import create_output_driver
from tmba.audio.pipeline_config import PipelineConfig
from tmba.audio.pipeline_stage import PipelineStage
from tmba.audio.stages import (
    EqualizerStage,
    LimiterStage,
    LoudnessStage,
    OutputStage,
    ReplayGainStage,
    SourceGainStage,
)


class PipelineState(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class PipelineStatus:
    state: PipelineState
    stage_count: int
    enabled_stage_count: int
    output: dict[str, object]
    stages: list[dict[str, object]]
    config: dict[str, object]


class AudioPipeline:
    """
    Logical TMBA audio pipeline.

    The output driver is selected through the configured driver factory unless
    a driver instance is injected explicitly for testing.
    """

    def __init__(
        self,
        *,
        config: PipelineConfig | None = None,
        output_driver: OutputDriver | None = None,
        stages: Iterable[PipelineStage] | None = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.output_driver = (
            output_driver
            if output_driver is not None
            else create_output_driver(self.config.output)
        )
        self._stages = (
            list(stages)
            if stages is not None
            else self._default_stages()
        )
        self._state = PipelineState.CREATED
        self._assign_order()
        self.validate()

    @property
    def state(self) -> PipelineState:
        return self._state

    @property
    def stages(self) -> tuple[PipelineStage, ...]:
        return tuple(self._stages)

    def _default_stages(self) -> list[PipelineStage]:
        return [
            SourceGainStage(self.config),
            ReplayGainStage(self.config),
            LoudnessStage(self.config),
            EqualizerStage(self.config),
            LimiterStage(self.config),
            OutputStage(self.config),
        ]

    def _assign_order(self) -> None:
        for index, stage in enumerate(self._stages):
            stage.set_order(index)

    def validate(self) -> None:
        names = [stage.name for stage in self._stages]
        if len(names) != len(set(names)):
            raise ValueError(
                "Pipeline stage names must be unique."
            )

        output_stages = [
            stage
            for stage in self._stages
            if stage.stage_type == "output"
        ]
        if len(output_stages) != 1:
            raise ValueError(
                "AudioPipeline requires exactly one output stage."
            )
        if self._stages[-1].stage_type != "output":
            raise ValueError(
                "The output stage must be the final pipeline stage."
            )

    def prepare(self) -> None:
        for stage in self._stages:
            stage.prepare()
        self._state = PipelineState.READY

    def start(self) -> None:
        try:
            self.prepare()
            self.output_driver.start()
            for stage in self._stages:
                stage.activate()
            self._state = PipelineState.RUNNING
        except Exception:
            self._state = PipelineState.ERROR
            raise

    def stop(self) -> None:
        self.output_driver.stop()
        for stage in self._stages:
            stage.reset()
        self._state = PipelineState.STOPPED

    def get_stage(self, name: str) -> PipelineStage:
        for stage in self._stages:
            if stage.name == name:
                return stage
        raise KeyError(
            f"Unknown pipeline stage: {name}"
        )

    def enable_stage(self, name: str) -> None:
        stage = self.get_stage(name)
        if stage.stage_type == "output":
            raise ValueError(
                "The output stage cannot be disabled "
                "or enabled manually."
            )
        stage.enable()

    def disable_stage(self, name: str) -> None:
        stage = self.get_stage(name)
        if stage.stage_type == "output":
            raise ValueError(
                "The output stage cannot be disabled."
            )
        stage.disable()

    def status(self) -> PipelineStatus:
        stage_statuses = [
            asdict(stage.status())
            for stage in self._stages
        ]
        output_status = asdict(
            self.output_driver.status()
        )
        return PipelineStatus(
            state=self._state,
            stage_count=len(self._stages),
            enabled_stage_count=sum(
                stage.enabled
                for stage in self._stages
            ),
            output=output_status,
            stages=stage_statuses,
            config=self.config.to_dict(),
        )
