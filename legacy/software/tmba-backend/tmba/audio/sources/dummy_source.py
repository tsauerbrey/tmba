"""Controllable sine-wave source for end-to-end TMBA audio tests."""

from __future__ import annotations

import time
from threading import Event, RLock, Thread, current_thread
from typing import Callable

from tmba.audio.engine_state import EngineSource
from tmba.audio.sources.base import (
    AudioSource,
    SourceCapabilities,
    SourceLifecycleState,
    SourceStatus,
)
from tmba.audio.sources.pcm_generator import PcmFormat, SineWaveGenerator


PcmWriter = Callable[[bytes], int]


class DummySource(AudioSource):
    """Generate paced PCM blocks on a background thread."""

    def __init__(
        self,
        writer: PcmWriter,
        *,
        frequency_hz: float = 440.0,
        amplitude: float = 0.20,
        pcm_format: PcmFormat | None = None,
        frames_per_block: int = 960,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if frames_per_block <= 0:
            raise ValueError("frames_per_block must be greater than zero.")
        self._writer = writer
        self._generator = SineWaveGenerator(
            frequency_hz=frequency_hz,
            amplitude=amplitude,
            pcm_format=pcm_format,
        )
        self._frames_per_block = int(frames_per_block)
        self._sleeper = sleeper
        self._state = SourceLifecycleState.DISCONNECTED
        self._connected = False
        self._active = False
        self._error: str | None = None
        self._bytes_written = 0
        self._blocks_written = 0
        self._stop_event = Event()
        self._pause_event = Event()
        self._thread: Thread | None = None
        self._lock = RLock()

    @property
    def source(self) -> EngineSource:
        return EngineSource.DUMMY

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            can_pause=True,
            can_resume=True,
            provides_pcm=True,
            provides_metadata=False,
            externally_controlled=False,
        )

    def connect(self) -> SourceStatus:
        with self._lock:
            if self._connected:
                return self.status()
            self._state = SourceLifecycleState.CONNECTING
            self._connected = True
            self._state = SourceLifecycleState.READY
            self._error = None
        return self.status()

    def disconnect(self) -> SourceStatus:
        self.stop()
        with self._lock:
            self._connected = False
            self._active = False
            self._state = SourceLifecycleState.DISCONNECTED
            self._error = None
        return self.status()

    def start(self) -> SourceStatus:
        with self._lock:
            if not self._connected:
                self.connect()
            if self._thread is not None and self._thread.is_alive():
                self._pause_event.clear()
                self._active = True
                self._state = SourceLifecycleState.PLAYING
                return self.status()

            self._state = SourceLifecycleState.STARTING
            self._error = None
            self._stop_event.clear()
            self._pause_event.clear()
            self._active = True
            self._thread = Thread(
                target=self._run,
                name="tmba-dummy-source",
                daemon=True,
            )
            self._thread.start()
            self._state = SourceLifecycleState.PLAYING
        return self.status()

    def stop(self) -> SourceStatus:
        with self._lock:
            thread = self._thread
            if thread is None:
                if self._connected:
                    self._state = SourceLifecycleState.READY
                self._active = False
                return self.status()
            self._state = SourceLifecycleState.STOPPING
            self._stop_event.set()
            self._pause_event.clear()

        if thread is not current_thread():
            thread.join(timeout=2.0)

        with self._lock:
            if thread.is_alive():
                self._state = SourceLifecycleState.ERROR
                self._error = "DummySource-Thread konnte nicht beendet werden."
            else:
                self._thread = None
                self._active = False
                self._state = (
                    SourceLifecycleState.READY
                    if self._connected
                    else SourceLifecycleState.DISCONNECTED
                )
        return self.status()

    def pause(self) -> SourceStatus:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                raise RuntimeError("DummySource spielt derzeit nicht.")
            self._pause_event.set()
            self._active = True
            self._state = SourceLifecycleState.PAUSED
        return self.status()

    def resume(self) -> SourceStatus:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                raise RuntimeError("DummySource wurde noch nicht gestartet.")
            self._pause_event.clear()
            self._active = True
            self._state = SourceLifecycleState.PLAYING
        return self.status()

    def status(self) -> SourceStatus:
        with self._lock:
            pcm_format = self._generator.pcm_format
            return SourceStatus(
                source=self.source,
                state=self._state,
                connected=self._connected,
                active=self._active,
                error=self._error,
                metadata={},
                details={
                    "implementation": "dummy",
                    "frequency_hz": self._generator.frequency_hz,
                    "amplitude": self._generator.amplitude,
                    "sample_rate": pcm_format.sample_rate,
                    "channels": pcm_format.channels,
                    "sample_format": pcm_format.sample_format,
                    "frames_per_block": self._frames_per_block,
                    "bytes_written": self._bytes_written,
                    "blocks_written": self._blocks_written,
                    "thread_alive": bool(
                        self._thread is not None and self._thread.is_alive()
                    ),
                },
            )

    def _run(self) -> None:
        block_duration = self._frames_per_block / self._generator.pcm_format.sample_rate
        try:
            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    self._sleeper(min(block_duration, 0.02))
                    continue

                block = self._generator.generate_frames(self._frames_per_block)
                written = self._writer(block)
                with self._lock:
                    self._bytes_written += int(written)
                    self._blocks_written += 1
                self._sleeper(block_duration)
        except Exception as error:
            with self._lock:
                self._error = str(error)
                self._state = SourceLifecycleState.ERROR
                self._active = False
            self._stop_event.set()
