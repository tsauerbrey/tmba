"""Central audio source coordinator for TMBA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import RLock
from time import monotonic
from typing import Any, Protocol

from tmba.audio.pipeline import AudioPipeline
from tmba.audio.pipeline_config import PipelineConfig
from tmba.audio.volume import SoftwareVolume
from tmba.core.config import get_settings
from tmba.core.event_bus import event_bus
from tmba.core.source_manager import source_manager


class AudioSourceService(Protocol):
    """Common commands supported by TMBA source services."""

    def get_status(self) -> dict[str, Any]:
        ...

    def play(self) -> dict[str, Any]:
        ...

    def pause(self) -> dict[str, Any]:
        ...

    def stop(self) -> dict[str, Any]:
        ...

    def previous(self) -> dict[str, Any]:
        ...

    def next(self) -> dict[str, Any]:
        ...

    def set_volume(self, volume: int) -> dict[str, Any]:
        ...


class AudioPipelineService(Protocol):
    """Lifecycle contract used by AudioManager."""

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def status(self) -> Any:
        ...

    def set_volume(self, volume: int) -> dict[str, Any]:
        ...

    def set_muted(self, muted: bool) -> dict[str, Any]:
        ...

    def toggle_muted(self) -> dict[str, Any]:
        ...

    def volume_status(self) -> dict[str, Any]:
        ...


@dataclass
class AudioManagerState:
    """Current state of the central TMBA audio pipeline."""

    source: str = "none"
    state: str = "stopped"
    volume: int = 50
    error: str | None = None
    transition_started_at: float | None = None
    output: str = "prepared"
    dsp: str = "prepared"


class AudioManager:
    """
    Coordinates all audio sources through one central state machine.

    TMBA v0.6.1-B connects the source coordinator to the logical
    AudioPipeline. The pipeline still uses NullOutputDriver by default and
    therefore does not open ALSA or CamillaDSP devices.
    """

    VALID_STATES = {
        "stopped",
        "starting",
        "playing",
        "paused",
        "error",
    }

    SUPPORTED_SOURCES = {
        "none",
        "webradio",
        "bluetooth",
        "airplay",
    }

    def __init__(
        self,
        *,
        pipeline: AudioPipelineService | None = None,
        initial_volume: int = 50,
    ) -> None:
        self._lock = RLock()
        self._state = AudioManagerState(volume=self._normalize_volume(initial_volume))
        self._services: dict[str, AudioSourceService] = {}
        self._pipeline = pipeline or AudioPipeline()
        if hasattr(self._pipeline, "set_volume"):
            self._pipeline.set_volume(self._state.volume)

        event_bus.subscribe(
            "source.availability_changed",
            self._handle_source_availability_changed,
        )

    @property
    def pipeline(self) -> AudioPipelineService:
        """Return the pipeline instance managed by this AudioManager."""

        return self._pipeline

    def register_source(
        self,
        source: str,
        service: AudioSourceService,
    ) -> None:
        """Register or replace the service used for an audio source."""

        normalized = self._normalize_source(source)

        if normalized == "none":
            raise ValueError(
                "Für die Quelle 'none' kann kein Dienst registriert werden."
            )

        with self._lock:
            self._services[normalized] = service

    def unregister_source(self, source: str) -> None:
        """Remove a previously registered source service."""

        normalized = self._normalize_source(source)

        with self._lock:
            self._services.pop(normalized, None)

    def get_status(self) -> dict[str, Any]:
        """Return a stable snapshot of manager and source state."""

        with self._lock:
            snapshot = asdict(self._state)
            registered_sources = sorted(self._services)

        source_status: dict[str, Any] | None = None

        if snapshot["source"] != "none":
            service = self._get_service(snapshot["source"])
            if service is not None:
                try:
                    source_status = service.get_status()
                except Exception as error:
                    source_status = {
                        "error": str(error),
                    }

        volume_status = None
        if hasattr(self._pipeline, "volume_status"):
            volume_status = self._pipeline.volume_status()
            snapshot["volume"] = int(volume_status.get("volume", snapshot["volume"]))
            snapshot["muted"] = bool(volume_status.get("muted", False))
            snapshot["gain_db"] = volume_status.get("gain_db")

        snapshot.update(
            {
                "registered_sources": registered_sources,
                "source_status": source_status,
                "transition_active": (
                    snapshot["state"] == "starting"
                ),
            }
        )

        return snapshot

    def get_pipeline_status(self) -> dict[str, Any]:
        """
        Return the current logical pipeline state.

        The dedicated REST endpoint is intentionally added only in v0.6.1-C.
        """

        status = self._pipeline.status()

        if hasattr(status, "__dataclass_fields__"):
            return asdict(status)

        if isinstance(status, dict):
            return dict(status)

        raise TypeError("Die AudioPipeline liefert keinen unterstützten Status.")

    def select_source(
        self,
        source: str,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Activate one source exclusively.

        The previously active source is stopped before the new source is
        selected. Selecting ``none`` stops the current source and pipeline.
        """

        target = self._normalize_source(source)

        with self._lock:
            previous = self._state.source

            if target == previous and not force:
                return self._result(
                    success=True,
                    message=f"Quelle {target} ist bereits aktiv.",
                    previous_source=previous,
                )

            self._set_state(
                state="starting",
                error=None,
                transition_started_at=monotonic(),
            )

        if previous != "none":
            stop_result = self._stop_source(previous)

            if not stop_result.get("success", False):
                return self._fail_transition(
                    (
                        f"Die bisherige Quelle {previous} konnte "
                        "nicht gestoppt werden."
                    ),
                    details=stop_result,
                    previous_source=previous,
                )

            pipeline_stop_error = self._try_stop_pipeline()
            if pipeline_stop_error is not None:
                return self._fail_transition(
                    "Die AudioPipeline konnte beim Quellenwechsel "
                    "nicht gestoppt werden.",
                    details={"error": pipeline_stop_error},
                    previous_source=previous,
                )

        if target == "none":
            if previous == "none":
                pipeline_stop_error = self._try_stop_pipeline()
                if pipeline_stop_error is not None:
                    return self._fail_transition(
                        "Die AudioPipeline konnte nicht gestoppt werden.",
                        details={"error": pipeline_stop_error},
                        previous_source=previous,
                    )

            source_manager.select_source("none")
            self._set_state(
                source="none",
                state="stopped",
                error=None,
                transition_started_at=None,
            )

            self._publish_source_changed(previous, "none")

            return self._result(
                success=True,
                message="Audioausgabe gestoppt.",
                previous_source=previous,
            )

        service = self._get_service(target)
        if service is None:
            return self._fail_transition(
                f"Für die Quelle {target} ist kein Dienst registriert.",
                previous_source=previous,
            )

        source_manager.select_source(target)

        self._set_state(
            source=target,
            state="stopped",
            error=None,
            transition_started_at=None,
        )

        self._publish_source_changed(previous, target)

        return self._result(
            success=True,
            message=f"Quelle {target} wurde aktiviert.",
            previous_source=previous,
        )

    def play(self) -> dict[str, Any]:
        return self._run_transport(
            "play",
            success_state="playing",
            start_pipeline=True,
        )

    def pause(self) -> dict[str, Any]:
        return self._run_transport("pause", success_state="paused")

    def stop(self) -> dict[str, Any]:
        with self._lock:
            source = self._state.source

        if source == "none":
            pipeline_stop_error = self._try_stop_pipeline()
            if pipeline_stop_error is not None:
                return self._set_error(
                    f"AudioPipeline konnte nicht gestoppt werden: "
                    f"{pipeline_stop_error}",
                    command="stop",
                )

            self._set_state(state="stopped", error=None)
            return self._result(
                success=True,
                message="Es ist keine Audioquelle aktiv.",
            )

        result = self._stop_source(source)

        if not result.get("success", False):
            return self._set_error_from_result("stop", result)

        pipeline_stop_error = self._try_stop_pipeline()
        if pipeline_stop_error is not None:
            return self._set_error(
                f"AudioPipeline konnte nicht gestoppt werden: "
                f"{pipeline_stop_error}",
                command="stop",
                service_result=result,
            )

        self._set_state(state="stopped", error=None)
        self._publish_state_changed("stopped")
        return self._result(
            success=True,
            command="stop",
            service_result=result,
        )

    def previous(self) -> dict[str, Any]:
        return self._run_transport(
            "previous",
            success_state=None,
        )

    def next(self) -> dict[str, Any]:
        return self._run_transport(
            "next",
            success_state=None,
        )

    def set_volume(self, volume: int) -> dict[str, Any]:
        normalized = self._normalize_volume(volume)

        pipeline_volume = None
        if hasattr(self._pipeline, "set_volume"):
            pipeline_volume = self._pipeline.set_volume(normalized)
            normalized = int(pipeline_volume.get("volume", normalized))

        with self._lock:
            source = self._state.source
            self._state.volume = normalized

        service_result: dict[str, Any] | None = None

        if source != "none":
            service = self._get_service(source)

            if service is not None and hasattr(service, "set_volume"):
                try:
                    service_result = service.set_volume(normalized)
                except Exception as error:
                    return self._set_error(
                        f"Lautstärke konnte nicht gesetzt werden: {error}",
                        command="set_volume",
                    )

                if not service_result.get("success", False):
                    return self._set_error_from_result(
                        "set_volume",
                        service_result,
                    )

        event_bus.publish(
            "audio.volume_changed",
            {
                "source": source,
                "volume": normalized,
            },
        )

        return self._result(
            success=True,
            command="set_volume",
            volume=normalized,
            service_result=service_result,
            volume_control=pipeline_volume,
        )

    def set_muted(self, muted: bool) -> dict[str, Any]:
        if not hasattr(self._pipeline, "set_muted"):
            return self._set_error("AudioPipeline unterstützt Mute nicht.")
        status = self._pipeline.set_muted(muted)
        event_bus.publish("audio.mute_changed", status)
        return self._result(
            success=True,
            command="set_muted",
            muted=bool(status["muted"]),
            volume_control=status,
        )

    def toggle_muted(self) -> dict[str, Any]:
        if not hasattr(self._pipeline, "toggle_muted"):
            return self._set_error("AudioPipeline unterstützt Mute nicht.")
        status = self._pipeline.toggle_muted()
        event_bus.publish("audio.mute_changed", status)
        return self._result(
            success=True,
            command="toggle_muted",
            muted=bool(status["muted"]),
            volume_control=status,
        )

    def synchronize(self) -> dict[str, Any]:
        """
        Synchronize manager state from the active source service.

        This is used by polling endpoints until source services publish all
        playback changes directly through the EventBus.
        """

        with self._lock:
            source = self._state.source

        if source == "none":
            return self._result(
                success=True,
                message="Keine aktive Quelle zu synchronisieren.",
            )

        service = self._get_service(source)
        if service is None:
            return self._set_error(
                f"Für die Quelle {source} ist kein Dienst registriert."
            )

        try:
            source_status = service.get_status()
        except Exception as error:
            return self._set_error(
                f"Quellenstatus konnte nicht gelesen werden: {error}"
            )

        playback_status = str(
            source_status.get("playback_status")
            or source_status.get("status")
            or "stopped"
        ).strip().lower()

        state_mapping = {
            "idle": "stopped",
            "stop": "stopped",
            "stopped": "stopped",
            "starting": "starting",
            "play": "playing",
            "playing": "playing",
            "pause": "paused",
            "paused": "paused",
            "error": "error",
        }

        mapped_state = state_mapping.get(playback_status, "stopped")
        self._set_state(state=mapped_state)

        return self._result(
            success=True,
            source_status=source_status,
        )

    def _run_transport(
        self,
        command: str,
        *,
        success_state: str | None,
        start_pipeline: bool = False,
    ) -> dict[str, Any]:
        with self._lock:
            source = self._state.source

        if source == "none":
            return self._set_error(
                "Es ist keine Audioquelle aktiv.",
                command=command,
            )

        service = self._get_service(source)
        if service is None:
            return self._set_error(
                f"Für die Quelle {source} ist kein Dienst registriert.",
                command=command,
            )

        method = getattr(service, command, None)
        if method is None:
            return self._set_error(
                f"Die Quelle {source} unterstützt {command} nicht.",
                command=command,
            )

        try:
            result = method()
        except Exception as error:
            return self._set_error(
                f"Audio-Befehl {command} ist fehlgeschlagen: {error}",
                command=command,
            )

        if not result.get("success", False):
            return self._set_error_from_result(command, result)

        if start_pipeline:
            try:
                self._pipeline.start()
            except Exception as error:
                rollback_result = self._stop_source(source)
                return self._set_error(
                    f"AudioPipeline konnte nicht gestartet werden: {error}",
                    command=command,
                    service_result=result,
                    rollback_result=rollback_result,
                )

        if success_state is not None:
            self._set_state(state=success_state, error=None)
            self._publish_state_changed(success_state)

        return self._result(
            success=True,
            command=command,
            service_result=result,
        )

    def _stop_source(self, source: str) -> dict[str, Any]:
        service = self._get_service(source)

        if service is None:
            return {
                "success": True,
                "message": (
                    f"Für {source} war kein Dienst registriert; "
                    "die Quelle gilt als gestoppt."
                ),
            }

        try:
            result = service.stop()
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }

        return result

    def _try_stop_pipeline(self) -> str | None:
        try:
            self._pipeline.stop()
        except Exception as error:
            return str(error)

        return None

    def _get_service(
        self,
        source: str,
    ) -> AudioSourceService | None:
        with self._lock:
            return self._services.get(source)

    def _handle_source_availability_changed(
        self,
        data: dict[str, Any],
    ) -> None:
        source = str(data.get("source", "")).strip().lower()
        available = data.get("available")

        if (
            source not in self.SUPPORTED_SOURCES
            or source == "none"
            or not isinstance(available, bool)
        ):
            return

        with self._lock:
            active_source = self._state.source

        if not available and active_source == source:
            self.select_source("none")

    def _fail_transition(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        previous_source: str | None = None,
    ) -> dict[str, Any]:
        self._set_state(
            state="error",
            error=message,
            transition_started_at=None,
        )

        event_bus.publish(
            "audio.error",
            {
                "source": self._state.source,
                "error": message,
            },
        )

        return self._result(
            success=False,
            error=message,
            details=details,
            previous_source=previous_source,
        )

    def _set_error_from_result(
        self,
        command: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        message = str(
            result.get("error")
            or result.get("message")
            or f"Audio-Befehl {command} ist fehlgeschlagen."
        )

        return self._set_error(
            message,
            command=command,
            service_result=result,
        )

    def _set_error(
        self,
        message: str,
        **extra: Any,
    ) -> dict[str, Any]:
        self._set_state(state="error", error=message)

        event_bus.publish(
            "audio.error",
            {
                "source": self._state.source,
                "error": message,
            },
        )

        return self._result(
            success=False,
            error=message,
            **extra,
        )

    def _set_state(self, **changes: Any) -> None:
        with self._lock:
            for key, value in changes.items():
                setattr(self._state, key, value)

    def _publish_source_changed(
        self,
        previous_source: str,
        source: str,
    ) -> None:
        event_bus.publish(
            "audio.source_changed",
            {
                "source": source,
                "previous_source": previous_source,
            },
        )

    def _publish_state_changed(self, state: str) -> None:
        event_bus.publish(
            "audio.state_changed",
            {
                "source": self._state.source,
                "state": state,
            },
        )

    def _result(
        self,
        *,
        success: bool,
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "success": success,
            "audio": self.get_status(),
            **extra,
        }

    def _normalize_source(self, source: str) -> str:
        normalized = str(source).strip().lower()

        if normalized not in self.SUPPORTED_SOURCES:
            raise ValueError(f"Unbekannte Audioquelle: {normalized}")

        return normalized

    @staticmethod
    def _normalize_volume(volume: Any) -> int:
        try:
            numeric = int(float(volume))
        except (TypeError, ValueError):
            numeric = 0

        return max(0, min(100, numeric))


_audio_settings = get_settings().audio
_volume_settings = _audio_settings.volume
_audio_pipeline = AudioPipeline(
    config=PipelineConfig.from_settings(),
    volume_control=SoftwareVolume(
        startup=int(_volume_settings.startup),
        minimum=int(_volume_settings.minimum),
        maximum=int(_volume_settings.maximum),
    ),
)
audio_manager = AudioManager(
    pipeline=_audio_pipeline,
    initial_volume=int(_volume_settings.startup),
)


def register_default_sources() -> None:
    """
    Register existing services after the manager singleton exists.

    Imports stay local to avoid circular imports during application start.
    """

    from tmba.services.airplay_service import airplay_service
    from tmba.services.bluetooth_service import bluetooth_service
    from tmba.services.webradio_service import webradio_service

    audio_manager.register_source("airplay", airplay_service)
    audio_manager.register_source("bluetooth", bluetooth_service)
    audio_manager.register_source("webradio", webradio_service)

