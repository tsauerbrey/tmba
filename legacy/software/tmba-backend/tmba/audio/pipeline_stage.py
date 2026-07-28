from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class StageState(str, Enum):
    """Runtime state of a pipeline stage."""

    CREATED = "created"
    READY = "ready"
    ACTIVE = "active"
    BYPASSED = "bypassed"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class StageStatus:
    """Serializable status snapshot for a pipeline stage."""

    name: str
    stage_type: str
    enabled: bool
    state: StageState
    order: int
    details: Mapping[str, Any]


class PipelineStage(ABC):
    """
    Base class for every logical stage in the TMBA audio pipeline.

    v0.6.1-A intentionally models architecture and state only. No audio
    samples are processed yet.
    """

    stage_type = "generic"

    def __init__(self, name: str, *, enabled: bool = True) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("A pipeline stage requires a non-empty name.")

        self._name = normalized
        self._enabled = bool(enabled)
        self._state = StageState.CREATED
        self._order = -1
        self._details: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def state(self) -> StageState:
        return self._state

    @property
    def order(self) -> int:
        return self._order

    def set_order(self, order: int) -> None:
        if order < 0:
            raise ValueError("Stage order must be zero or greater.")
        self._order = order

    def enable(self) -> None:
        self._enabled = True
        self._state = StageState.READY

    def disable(self) -> None:
        self._enabled = False
        self._state = StageState.BYPASSED

    def prepare(self) -> None:
        self._state = StageState.READY if self._enabled else StageState.BYPASSED

    def activate(self) -> None:
        self._state = StageState.ACTIVE if self._enabled else StageState.BYPASSED

    def reset(self) -> None:
        self._state = StageState.CREATED
        self._details.clear()

    def set_error(self, message: str) -> None:
        self._state = StageState.ERROR
        self._details["error"] = message

    def set_detail(self, key: str, value: Any) -> None:
        self._details[key] = value

    def status(self) -> StageStatus:
        return StageStatus(
            name=self._name,
            stage_type=self.stage_type,
            enabled=self._enabled,
            state=self._state,
            order=self._order,
            details=dict(self._details),
        )
