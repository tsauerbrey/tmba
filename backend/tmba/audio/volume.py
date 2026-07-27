"""Volume controllers for TMBA.

TMBA v0.9.5 uses one master-volume controller for every audio source.
On the production Raspberry Pi this is the HiFiBerry ALSA mixer.
"""
from __future__ import annotations

from array import array
from dataclasses import asdict, dataclass
from math import pow
import re
import subprocess
from sys import byteorder
from threading import RLock
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class VolumeStatus:
    volume: int
    muted: bool
    gain_db: float
    gain_linear: float
    minimum: int
    maximum: int
    driver: str
    device: str = ""
    control: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class VolumeController(Protocol):
    def set_volume(self, volume: int) -> VolumeStatus: ...
    def set_muted(self, muted: bool) -> VolumeStatus: ...
    def toggle_muted(self) -> VolumeStatus: ...
    def status(self) -> VolumeStatus: ...
    def apply_s16le(self, pcm_data: bytes) -> bytes: ...


class SoftwareVolume:
    """Software fallback used by tests and non-HiFiBerry systems."""

    MIN_GAIN_DB = -60.0

    def __init__(
        self,
        *,
        startup: int = 25,
        minimum: int = 0,
        maximum: int = 100,
    ) -> None:
        if not 0 <= minimum <= startup <= maximum <= 100:
            raise ValueError(
                "Lautstärke muss minimum <= startup <= maximum <= 100 erfüllen."
            )
        self._lock = RLock()
        self._minimum = int(minimum)
        self._maximum = int(maximum)
        self._volume = int(startup)
        self._muted = self._volume == 0

    def set_volume(self, volume: int) -> VolumeStatus:
        with self._lock:
            self._volume = max(self._minimum, min(self._maximum, int(volume)))
            if self._volume > 0:
                self._muted = False
            return self.status()

    def set_muted(self, muted: bool) -> VolumeStatus:
        with self._lock:
            self._muted = bool(muted)
            return self.status()

    def toggle_muted(self) -> VolumeStatus:
        with self._lock:
            self._muted = not self._muted
            return self.status()

    def status(self) -> VolumeStatus:
        with self._lock:
            gain_db = self._gain_db_locked()
            gain_linear = 0.0 if self._muted else pow(10.0, gain_db / 20.0)
            return VolumeStatus(
                volume=self._volume,
                muted=self._muted,
                gain_db=round(gain_db, 2),
                gain_linear=round(gain_linear, 6),
                minimum=self._minimum,
                maximum=self._maximum,
                driver="software",
            )

    def apply_s16le(self, pcm_data: bytes) -> bytes:
        if len(pcm_data) % 2:
            raise ValueError("S16_LE-PCM muss eine gerade Byteanzahl besitzen.")
        status = self.status()
        if status.muted or status.volume == 0:
            return bytes(len(pcm_data))
        if status.gain_linear >= 0.999999:
            return pcm_data

        samples = array("h")
        samples.frombytes(pcm_data)
        if byteorder != "little":
            samples.byteswap()

        gain = status.gain_linear
        for index, sample in enumerate(samples):
            scaled = round(sample * gain)
            samples[index] = max(-32768, min(32767, scaled))

        if byteorder != "little":
            samples.byteswap()
        return samples.tobytes()

    def _gain_db_locked(self) -> float:
        if self._muted or self._volume <= 0:
            return self.MIN_GAIN_DB
        return -40.0 * (1.0 - self._volume / 100.0)


class AlsaMixerError(RuntimeError):
    """Raised when the configured ALSA mixer cannot be used."""


class AlsaMixerVolume:
    """HiFiBerry master volume backed by ``amixer``."""

    _PERCENT = re.compile(r"\[(\d{1,3})%\]")
    _DB = re.compile(r"\[(-?\d+(?:\.\d+)?)dB\]")
    _SWITCH = re.compile(r"\[(on|off)\]", re.IGNORECASE)

    def __init__(
        self,
        *,
        card: str = "sndrpihifiberry",
        control: str = "Digital",
        minimum: int = 0,
        maximum: int = 100,
        command: str = "amixer",
        validate: bool = True,
    ) -> None:
        if not 0 <= minimum <= maximum <= 100:
            raise ValueError("0 <= minimum <= maximum <= 100 ist erforderlich.")
        self._lock = RLock()
        self._card = card
        self._control = control
        self._minimum = int(minimum)
        self._maximum = int(maximum)
        self._command = command
        if validate:
            self.status()

    def set_volume(self, volume: int) -> VolumeStatus:
        value = max(self._minimum, min(self._maximum, int(volume)))
        with self._lock:
            self._run("sset", self._control, f"{value}%")
            if value > 0:
                self._run("sset", self._control, "unmute")
            return self.status()

    def set_muted(self, muted: bool) -> VolumeStatus:
        with self._lock:
            self._run("sset", self._control, "mute" if muted else "unmute")
            return self.status()

    def toggle_muted(self) -> VolumeStatus:
        return self.set_muted(not self.status().muted)

    def status(self) -> VolumeStatus:
        output = self._run("sget", self._control)
        percentages = [int(x) for x in self._PERCENT.findall(output)]
        if not percentages:
            raise AlsaMixerError(
                f"ALSA-Regler {self._control!r} liefert keinen Prozentwert."
            )
        switches = [x.lower() for x in self._SWITCH.findall(output)]
        muted = bool(switches) and all(x == "off" for x in switches)
        db_values = [float(x) for x in self._DB.findall(output)]
        gain_db = sum(db_values) / len(db_values) if db_values else 0.0
        gain_linear = 0.0 if muted else pow(10.0, gain_db / 20.0)
        return VolumeStatus(
            volume=round(sum(percentages) / len(percentages)),
            muted=muted,
            gain_db=round(gain_db, 2),
            gain_linear=round(gain_linear, 6),
            minimum=self._minimum,
            maximum=self._maximum,
            driver="alsa",
            device=self._card,
            control=self._control,
        )

    def apply_s16le(self, pcm_data: bytes) -> bytes:
        if len(pcm_data) % 2:
            raise ValueError("S16_LE-PCM muss eine gerade Byteanzahl besitzen.")
        return pcm_data

    def _run(self, *arguments: str) -> str:
        command: Sequence[str] = (
            self._command, "-c", self._card, *arguments
        )
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=3.0,
            )
        except FileNotFoundError as exc:
            raise AlsaMixerError(
                f"ALSA-Werkzeug {self._command!r} wurde nicht gefunden."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise AlsaMixerError(
                "Zeitüberschreitung beim Zugriff auf den ALSA-Mixer."
            ) from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or str(exc)).strip()
            raise AlsaMixerError(f"ALSA-Mixerfehler: {details}") from exc
        return result.stdout
