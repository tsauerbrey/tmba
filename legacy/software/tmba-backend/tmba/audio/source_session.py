"""Immutable description of the currently selected audio source."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from tmba.audio.engine_state import EngineSource


@dataclass(frozen=True, slots=True)
class SourceSession:
    source: EngineSource
    activated_at: float

    @classmethod
    def create(cls, source: EngineSource) -> "SourceSession":
        return cls(source=source, activated_at=monotonic())
