"""Registry for concrete implementations of the common AudioSource API."""

from __future__ import annotations

from threading import RLock
from typing import Iterable

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources.base import AudioSource


class AudioSourceRegistry:
    """Thread-safe source registry used by later AudioEngine milestones."""

    def __init__(self, sources: Iterable[AudioSource] | None = None) -> None:
        self._lock = RLock()
        self._sources: dict[EngineSource, AudioSource] = {}
        for source in sources or ():
            self.register(source)

    def register(
        self,
        source: AudioSource,
        *,
        replace: bool = False,
    ) -> None:
        source_id = self._normalize(source.source)
        if source_id is EngineSource.NONE:
            raise ValueError("Die Pseudoquelle 'none' kann nicht registriert werden.")

        with self._lock:
            if source_id in self._sources and not replace:
                raise ValueError(
                    f"Quelle {source_id.value} ist bereits registriert."
                )
            self._sources[source_id] = source

    def unregister(self, source: EngineSource | str) -> AudioSource | None:
        source_id = self._normalize(source)
        with self._lock:
            return self._sources.pop(source_id, None)

    def get(self, source: EngineSource | str) -> AudioSource | None:
        source_id = self._normalize(source)
        with self._lock:
            return self._sources.get(source_id)

    def require(self, source: EngineSource | str) -> AudioSource:
        source_id = self._normalize(source)
        registered = self.get(source_id)
        if registered is None:
            raise LookupError(
                f"Für die Quelle {source_id.value} ist keine "
                "AudioSource-Implementierung registriert."
            )
        return registered

    def names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(source.value for source in self._sources))

    def statuses(self) -> dict[str, dict[str, object]]:
        with self._lock:
            snapshot = tuple(self._sources.items())
        return {
            source.value: implementation.status().to_dict()
            for source, implementation in snapshot
        }

    @staticmethod
    def _normalize(source: EngineSource | str) -> EngineSource:
        if isinstance(source, EngineSource):
            return source
        try:
            return EngineSource(str(source).strip().lower())
        except ValueError as error:
            raise ValueError(f"Unbekannte Audioquelle: {source}") from error
