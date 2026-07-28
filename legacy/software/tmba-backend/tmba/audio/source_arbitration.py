"""Priority-based source arbitration for the TMBA AudioEngine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping

from tmba.audio.engine_state import EngineSource


class ArbitrationAction(str, Enum):
    ACTIVATE = "activate"
    KEEP_CURRENT = "keep_current"
    REJECT = "reject"
    DEACTIVATE = "deactivate"


@dataclass(frozen=True, slots=True)
class ArbitrationDecision:
    action: ArbitrationAction
    requested_source: EngineSource
    current_source: EngineSource
    accepted: bool
    forced: bool
    requested_priority: int
    current_priority: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceArbitrator:
    """
    Decide whether a requested source may replace the current source.

    Higher numeric values have higher priority. ``none`` always deactivates
    the current source. ``force=True`` bypasses normal priority checks.
    """

    DEFAULT_PRIORITIES: Mapping[EngineSource, int] = {
        EngineSource.NONE: 0,
        EngineSource.DUMMY: 1,
        EngineSource.WEBRADIO: 10,
        EngineSource.BLUETOOTH: 20,
        EngineSource.AIRPLAY: 30,
    }

    def __init__(
        self,
        priorities: Mapping[EngineSource | str, int] | None = None,
    ) -> None:
        configured = dict(self.DEFAULT_PRIORITIES)
        if priorities:
            for source, priority in priorities.items():
                normalized = self._normalize_source(source)
                configured[normalized] = int(priority)
        configured[EngineSource.NONE] = 0
        self._priorities = configured

    def priority(self, source: EngineSource | str) -> int:
        return self._priorities[self._normalize_source(source)]

    def decide(
        self,
        current_source: EngineSource | str,
        requested_source: EngineSource | str,
        *,
        force: bool = False,
    ) -> ArbitrationDecision:
        current = self._normalize_source(current_source)
        requested = self._normalize_source(requested_source)
        current_priority = self.priority(current)
        requested_priority = self.priority(requested)

        if requested is EngineSource.NONE:
            return ArbitrationDecision(
                action=ArbitrationAction.DEACTIVATE,
                requested_source=requested,
                current_source=current,
                accepted=True,
                forced=force,
                requested_priority=requested_priority,
                current_priority=current_priority,
                reason="Die aktive Quelle wird deaktiviert.",
            )

        if requested is current and not force:
            return ArbitrationDecision(
                action=ArbitrationAction.KEEP_CURRENT,
                requested_source=requested,
                current_source=current,
                accepted=True,
                forced=False,
                requested_priority=requested_priority,
                current_priority=current_priority,
                reason=f"Quelle {requested.value} ist bereits aktiv.",
            )

        if force or current is EngineSource.NONE:
            reason = (
                "Der Quellenwechsel wurde erzwungen."
                if force and current is not EngineSource.NONE
                else "Es ist keine konkurrierende Quelle aktiv."
            )
            return ArbitrationDecision(
                action=ArbitrationAction.ACTIVATE,
                requested_source=requested,
                current_source=current,
                accepted=True,
                forced=force,
                requested_priority=requested_priority,
                current_priority=current_priority,
                reason=reason,
            )

        if requested_priority > current_priority:
            return ArbitrationDecision(
                action=ArbitrationAction.ACTIVATE,
                requested_source=requested,
                current_source=current,
                accepted=True,
                forced=False,
                requested_priority=requested_priority,
                current_priority=current_priority,
                reason=(
                    f"Quelle {requested.value} hat eine höhere Priorität "
                    f"als {current.value}."
                ),
            )

        return ArbitrationDecision(
            action=ArbitrationAction.REJECT,
            requested_source=requested,
            current_source=current,
            accepted=False,
            forced=False,
            requested_priority=requested_priority,
            current_priority=current_priority,
            reason=(
                f"Quelle {requested.value} hat keine höhere Priorität "
                f"als die aktive Quelle {current.value}."
            ),
        )

    def status(self) -> dict[str, int]:
        return {
            source.value: self._priorities[source]
            for source in EngineSource
        }

    @staticmethod
    def _normalize_source(source: EngineSource | str) -> EngineSource:
        if isinstance(source, EngineSource):
            return source
        try:
            return EngineSource(str(source).strip().lower())
        except ValueError as error:
            raise ValueError(f"Unbekannte Audioquelle: {source}") from error
