"""Software volume control for the fixed TMBA audio hardware."""

from __future__ import annotations

from array import array
from dataclasses import asdict, dataclass
from math import pow
from sys import byteorder
from threading import RLock


@dataclass(frozen=True, slots=True)
class VolumeStatus:
    volume: int
    muted: bool
    gain_db: float
    gain_linear: float
    minimum: int
    maximum: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class SoftwareVolume:
    """
    Apply a predictable digital volume curve to signed 16-bit stereo PCM.

    The Amp4 Pro overlay does not expose a dependable ALSA simple-mixer
    control on the target image. TMBA therefore owns the playback volume in
    software. The configured maximum remains below 100 to preserve headroom.
    """

    MIN_GAIN_DB = -60.0

    def __init__(
        self,
        *,
        startup: int = 25,
        minimum: int = 0,
        maximum: int = 90,
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
            else:
                self._muted = True
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
            )

    def apply_s16le(self, pcm_data: bytes) -> bytes:
        """Return volume-adjusted signed 16-bit little-endian PCM."""

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

        # 100 -> 0 dB, 50 -> -20 dB, 25 -> -30 dB.
        return -40.0 * (1.0 - (self._volume / 100.0))
