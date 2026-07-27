from __future__ import annotations

import subprocess
import pytest

from tmba.audio.volume import AlsaMixerError, AlsaMixerVolume

ON = """Simple mixer control 'Digital',0
  Capabilities: pvolume pswitch
  Playback channels: Front Left - Front Right
  Limits: Playback 0 - 207
  Front Left: Playback 124 [60%] [-41.50dB] [on]
  Front Right: Playback 124 [60%] [-41.50dB] [on]
"""
OFF = ON.replace("[on]", "[off]")


def test_status_parses_hifiberry_output(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, ON, "")
    )
    status = AlsaMixerVolume().status()
    assert status.volume == 60
    assert status.muted is False
    assert status.driver == "alsa"
    assert status.device == "sndrpihifiberry"
    assert status.control == "Digital"


def test_set_volume_uses_named_card_and_reads_back(monkeypatch):
    commands = []
    def fake(command, **kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, ON, "")
    monkeypatch.setattr(subprocess, "run", fake)
    control = AlsaMixerVolume()
    commands.clear()
    assert control.set_volume(30).volume == 60
    assert commands[0] == [
        "amixer", "-c", "sndrpihifiberry", "sset", "Digital", "30%"
    ]
    assert commands[1][-1] == "unmute"
    assert commands[2][-2:] == ["sget", "Digital"]


def test_mute_reads_real_switch_state(monkeypatch):
    muted = False
    def fake(command, **kwargs):
        nonlocal muted
        command = list(command)
        if command[-1] == "mute":
            muted = True
        elif command[-1] == "unmute":
            muted = False
        return subprocess.CompletedProcess(command, 0, OFF if muted else ON, "")
    monkeypatch.setattr(subprocess, "run", fake)
    control = AlsaMixerVolume()
    assert control.set_muted(True).muted is True
    assert control.set_muted(False).muted is False


def test_hardware_volume_does_not_attenuate_pcm_twice(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, ON, "")
    )
    control = AlsaMixerVolume()
    pcm = b"\x01\x00\x02\x00"
    assert control.apply_s16le(pcm) == pcm


def test_clear_error_when_control_is_missing(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(
            1, args[0], stderr="Unable to find simple control 'Digital',0"
        )
    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(AlsaMixerError, match="Digital"):
        AlsaMixerVolume()
