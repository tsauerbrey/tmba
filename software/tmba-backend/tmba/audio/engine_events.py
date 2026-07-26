"""Event names and payload helpers for the TMBA AudioEngine."""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any

ENGINE_STARTED = "audio.engine.started"
ENGINE_STOPPED = "audio.engine.stopped"
ENGINE_STATE_CHANGED = "audio.engine.state_changed"
ENGINE_SOURCE_CHANGED = "audio.engine.source_changed"
ENGINE_ERROR = "audio.engine.error"

ENGINE_ARBITRATION_ACCEPTED = "audio.engine.arbitration_accepted"
ENGINE_ARBITRATION_REJECTED = "audio.engine.arbitration_rejected"


@dataclass(frozen=True, slots=True)
class EngineEvent:
    event: str
    state: str
    source: str
    previous_state: str | None = None
    previous_source: str | None = None
    error: str | None = None
    timestamp: float = 0.0

    @classmethod
    def create(
        cls,
        event: str,
        *,
        state: str,
        source: str,
        previous_state: str | None = None,
        previous_source: str | None = None,
        error: str | None = None,
    ) -> "EngineEvent":
        return cls(
            event=event,
            state=state,
            source=source,
            previous_state=previous_state,
            previous_source=previous_source,
            error=error,
            timestamp=time(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "state": self.state,
            "source": self.source,
            "previous_state": self.previous_state,
            "previous_source": self.previous_source,
            "error": self.error,
            "timestamp": self.timestamp,
        }
