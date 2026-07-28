"""Central lifecycle facade for TMBA audio playback."""

from __future__ import annotations

from threading import RLock
from typing import Any, Protocol

from tmba.audio.engine_events import (
    ENGINE_ARBITRATION_ACCEPTED,
    ENGINE_ARBITRATION_REJECTED,
    ENGINE_ERROR,
    ENGINE_SOURCE_CHANGED,
    ENGINE_STARTED,
    ENGINE_STATE_CHANGED,
    ENGINE_STOPPED,
    EngineEvent,
)
from tmba.audio.engine_state import EngineSource, EngineState, EngineStatus
from tmba.audio.manager import AudioManager, audio_manager
from tmba.audio.source_arbitration import (
    ArbitrationDecision,
    SourceArbitrator,
)
from tmba.audio.source_session import SourceSession
from tmba.core.event_bus import EventBus, event_bus


class AudioManagerContract(Protocol):
    def get_status(self) -> dict[str, Any]: ...
    def get_pipeline_status(self) -> dict[str, Any]: ...
    def select_source(self, source: str, *, force: bool = False) -> dict[str, Any]: ...
    def play(self) -> dict[str, Any]: ...
    def pause(self) -> dict[str, Any]: ...
    def stop(self) -> dict[str, Any]: ...


class AudioEngine:
    """
    Stable application-facing facade around AudioManager and AudioPipeline.

    AudioManager continues to own transport commands and source services.
    AudioEngine adds a strict lifecycle, normalized status and engine events.
    """

    def __init__(
        self,
        *,
        manager: AudioManagerContract | None = None,
        bus: EventBus | None = None,
        arbitrator: SourceArbitrator | None = None,
    ) -> None:
        self._manager = manager or AudioManager()
        self._bus = bus or event_bus
        self._arbitrator = arbitrator or SourceArbitrator()
        self._lock = RLock()
        self._state = EngineState.STOPPED
        self._session = SourceSession.create(EngineSource.NONE)
        self._error: str | None = None

    @property
    def manager(self) -> AudioManagerContract:
        return self._manager

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._state in {
                EngineState.READY,
                EngineState.PLAYING,
                EngineState.PAUSED,
            }:
                return self._result(True, "AudioEngine ist bereits gestartet.")
            previous = self._state
            self._state = EngineState.STARTING
            self._error = None

        self._publish_state(previous)
        self._set_state(EngineState.READY)
        self._publish(
            ENGINE_STARTED,
            previous_state=previous.value,
        )
        return self._result(True, "AudioEngine wurde gestartet.")

    def stop(self) -> dict[str, Any]:
        with self._lock:
            previous_state = self._state
            previous_source = self._session.source
            self._state = EngineState.STOPPING

        self._publish_state(previous_state)

        source_result = self._manager.select_source("none")
        if not source_result.get("success", False):
            return self._fail(self._message_from_result(source_result))

        with self._lock:
            self._session = SourceSession.create(EngineSource.NONE)
            self._state = EngineState.STOPPED
            self._error = None

        if previous_source is not EngineSource.NONE:
            self._publish(
                ENGINE_SOURCE_CHANGED,
                previous_source=previous_source.value,
            )
        self._publish(
            ENGINE_STOPPED,
            previous_state=previous_state.value,
        )
        return self._result(True, "AudioEngine wurde gestoppt.")

    def activate_source(
        self,
        source: str | EngineSource,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        target = self._normalize_source(source)

        if self._state is EngineState.STOPPED:
            started = self.start()
            if not started.get("success", False):
                return started

        with self._lock:
            previous_source = self._session.source

        decision = self._arbitrator.decide(
            previous_source,
            target,
            force=force,
        )
        self._publish_arbitration(decision)

        if not decision.accepted:
            return self._rejected(decision.reason, decision)

        if decision.action.value == "keep_current":
            return self._result(
                True,
                decision.reason,
                arbitration=decision.to_dict(),
            )

        result = self._manager.select_source(target.value, force=force)
        if not result.get("success", False):
            return self._fail(self._message_from_result(result))

        with self._lock:
            self._session = SourceSession.create(target)
            self._error = None
            if target is EngineSource.NONE:
                self._state = EngineState.READY

        if target is not previous_source:
            self._publish(
                ENGINE_SOURCE_CHANGED,
                previous_source=previous_source.value,
            )
        return self._result(
            True,
            f"Quelle {target.value} wurde aktiviert.",
            arbitration=decision.to_dict(),
        )

    def deactivate_source(self) -> dict[str, Any]:
        return self.activate_source(EngineSource.NONE)

    def play(self) -> dict[str, Any]:
        if self._session.source is EngineSource.NONE:
            return self._fail("Es ist keine Audioquelle aktiv.")
        result = self._manager.play()
        if not result.get("success", False):
            return self._fail(self._message_from_result(result))
        self._set_state(EngineState.PLAYING)
        return self._result(True, "Wiedergabe wurde gestartet.")

    def pause(self) -> dict[str, Any]:
        if self._session.source is EngineSource.NONE:
            return self._fail("Es ist keine Audioquelle aktiv.")
        result = self._manager.pause()
        if not result.get("success", False):
            return self._fail(self._message_from_result(result))
        self._set_state(EngineState.PAUSED)
        return self._result(True, "Wiedergabe wurde pausiert.")

    def status(self) -> dict[str, Any]:
        manager_status = self._manager.get_status()
        pipeline_status = self._manager.get_pipeline_status()
        output = pipeline_status.get("output") or {}
        driver = str(output.get("driver", "unknown"))
        pipeline_state = pipeline_status.get("state", "unknown")
        if hasattr(pipeline_state, "value"):
            pipeline_state = pipeline_state.value

        with self._lock:
            status = EngineStatus(
                state=self._state,
                source=self._session.source,
                manager_state=str(manager_status.get("state", "unknown")),
                pipeline_state=str(pipeline_state),
                output_driver=driver,
                volume=int(manager_status.get("volume", 0)),
                error=self._error,
                transition_active=self._state in {
                    EngineState.STARTING,
                    EngineState.STOPPING,
                },
                registered_sources=tuple(
                    manager_status.get("registered_sources", [])
                ),
            )
        result = status.to_dict()
        result["source_priority"] = self._arbitrator.priority(
            self._session.source
        )
        result["source_priorities"] = self._arbitrator.status()
        return result

    def _set_state(self, state: EngineState) -> None:
        with self._lock:
            previous = self._state
            self._state = state
            self._error = None
        if state is not previous:
            self._publish_state(previous)

    def _fail(self, message: str) -> dict[str, Any]:
        with self._lock:
            previous = self._state
            self._state = EngineState.ERROR
            self._error = message
        self._publish_state(previous)
        self._publish(ENGINE_ERROR, previous_state=previous.value, error=message)
        return self._result(False, message)

    def _publish_state(self, previous: EngineState) -> None:
        self._publish(
            ENGINE_STATE_CHANGED,
            previous_state=previous.value,
        )

    def _publish(
        self,
        event_name: str,
        *,
        previous_state: str | None = None,
        previous_source: str | None = None,
        error: str | None = None,
    ) -> None:
        event = EngineEvent.create(
            event_name,
            state=self._state.value,
            source=self._session.source.value,
            previous_state=previous_state,
            previous_source=previous_source,
            error=error,
        )
        self._bus.publish(event_name, event.to_dict())

    def _result(
        self,
        success: bool,
        message: str,
        *,
        arbitration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "success": success,
            "message" if success else "error": message,
            "engine": self.status(),
        }
        if arbitration is not None:
            result["arbitration"] = arbitration
        return result

    def _rejected(
        self,
        message: str,
        decision: ArbitrationDecision,
    ) -> dict[str, Any]:
        return self._result(
            False,
            message,
            arbitration=decision.to_dict(),
        )

    def _publish_arbitration(
        self,
        decision: ArbitrationDecision,
    ) -> None:
        event_name = (
            ENGINE_ARBITRATION_ACCEPTED
            if decision.accepted
            else ENGINE_ARBITRATION_REJECTED
        )
        payload = decision.to_dict()
        payload["event"] = event_name
        payload["state"] = self._state.value
        self._bus.publish(event_name, payload)

    @staticmethod
    def _normalize_source(source: str | EngineSource) -> EngineSource:
        if isinstance(source, EngineSource):
            return source
        try:
            return EngineSource(str(source).strip().lower())
        except ValueError as error:
            raise ValueError(f"Unbekannte Audioquelle: {source}") from error

    @staticmethod
    def _message_from_result(result: dict[str, Any]) -> str:
        return str(
            result.get("error")
            or result.get("message")
            or "Audio-Befehl ist fehlgeschlagen."
        )


audio_engine = AudioEngine(manager=audio_manager)
