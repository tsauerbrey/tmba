"""State models used by the central TMBA AudioEngine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class EngineState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class EngineSource(str, Enum):
    NONE = "none"
    DUMMY = "dummy"
    AIRPLAY = "airplay"
    BLUETOOTH = "bluetooth"
    WEBRADIO = "webradio"


@dataclass(frozen=True, slots=True)
class EngineStatus:
    state: EngineState
    source: EngineSource
    manager_state: str
    pipeline_state: str
    output_driver: str
    volume: int
    error: str | None
    transition_active: bool
    registered_sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
