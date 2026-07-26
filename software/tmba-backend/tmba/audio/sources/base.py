"""Stable, implementation-independent contract for TMBA audio sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from tmba.audio.engine_state import EngineSource


class SourceLifecycleState(str, Enum):
    """Lifecycle states shared by every TMBA audio source."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    READY = "ready"
    STARTING = "starting"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SourceCapabilities:
    """Feature flags exposed to AudioEngine and future user interfaces."""

    can_pause: bool = True
    can_resume: bool = True
    provides_pcm: bool = False
    provides_metadata: bool = True
    externally_controlled: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SourceStatus:
    """Normalized snapshot returned by every source implementation."""

    source: EngineSource
    state: SourceLifecycleState
    connected: bool
    active: bool
    error: str | None = None
    metadata: dict[str, Any] | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["source"] = self.source.value
        result["state"] = self.state.value
        result["metadata"] = dict(self.metadata or {})
        result["details"] = dict(self.details or {})
        return result


class AudioSource(ABC):
    """
    Common lifecycle API for AirPlay, Bluetooth, Webradio and test sources.

    Implementations own their source-specific process or connection. They do
    not decide whether they may replace another source; source arbitration
    remains the responsibility of AudioEngine.
    """

    @property
    @abstractmethod
    def source(self) -> EngineSource:
        """Return the stable engine identifier for this source."""

    @property
    def name(self) -> str:
        return self.source.value

    @property
    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities()

    @abstractmethod
    def connect(self) -> SourceStatus:
        """Prepare the source and its external resources."""

    @abstractmethod
    def disconnect(self) -> SourceStatus:
        """Release all resources owned by the source."""

    @abstractmethod
    def start(self) -> SourceStatus:
        """Start or accept playback for this source."""

    @abstractmethod
    def stop(self) -> SourceStatus:
        """Stop playback while keeping the source available when possible."""

    def pause(self) -> SourceStatus:
        if not self.capabilities.can_pause:
            raise NotImplementedError(
                f"Quelle {self.name} unterstützt Pause nicht."
            )
        raise NotImplementedError(
            f"Quelle {self.name} hat Pause nicht implementiert."
        )

    def resume(self) -> SourceStatus:
        if not self.capabilities.can_resume:
            raise NotImplementedError(
                f"Quelle {self.name} unterstützt Fortsetzen nicht."
            )
        raise NotImplementedError(
            f"Quelle {self.name} hat Fortsetzen nicht implementiert."
        )

    @abstractmethod
    def status(self) -> SourceStatus:
        """Return a side-effect-free status snapshot."""
