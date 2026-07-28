from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class OutputState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class OutputStatus:
    driver: str
    state: OutputState
    device: str
    sample_rate: int
    channels: int
    format: str
    details: Mapping[str, Any]


class OutputDriver(ABC):
    """Abstract destination for the TMBA audio pipeline."""

    driver_name = "base"

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def write(self, pcm_data: bytes) -> int:
        """Write one block of raw PCM data and return bytes accepted."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> OutputStatus:
        raise NotImplementedError
