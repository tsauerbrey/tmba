from __future__ import annotations

import io
import subprocess

import pytest

from tmba.audio.outputs.alsa_output import (
    AlsaOutputDriver,
    AlsaOutputError,
)
from tmba.audio.pipeline_config import OutputConfig


APLAY_OUTPUT = """\
**** List of PLAYBACK Hardware Devices ****
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
card 1: sndrpihifiberry [snd_rpi_hifiberry_dacplus], device 0: HiFiBerry DAC+ Pro HiFi pcm512x-hifi-0 [HiFiBerry DAC+ Pro HiFi pcm512x-hifi-0]
"""


class FakeProcess:
    def __init__(self, *, exit_code: int | None = None) -> None:
        self.stdin = io.BytesIO()
        self.stderr = io.BytesIO()
        self.exit_code = exit_code
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.exit_code

    def terminate(self) -> None:
        self.terminated = True
        self.exit_code = 0

    def kill(self) -> None:
        self.killed = True
        self.exit_code = -9

    def wait(self, timeout: float | None = None) -> int:
        return 0 if self.exit_code is None else self.exit_code


def result(
    *,
    returncode: int = 0,
    stdout: str = APLAY_OUTPUT,
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["aplay", "-l"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def create_driver(
    *,
    process: FakeProcess | None = None,
    device: str = "hw:1,0",
    audio_format: str = "S32_LE",
) -> tuple[AlsaOutputDriver, FakeProcess, list[list[str]]]:
    playback = process or FakeProcess()
    commands: list[list[str]] = []

    def process_factory(command):
        commands.append(list(command))
        return playback

    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device=device,
            sample_rate=48_000,
            channels=2,
            format=audio_format,
        ),
        command_runner=lambda _: result(),
        process_factory=process_factory,
        platform_name="linux",
        executable_finder=lambda _: "/usr/bin/aplay",
    )
    return driver, playback, commands


def test_parse_aplay_device_list() -> None:
    devices = AlsaOutputDriver.parse_device_list(APLAY_OUTPUT)

    assert len(devices) == 2
    assert devices[0].hardware_address == "hw:0,0"
    assert devices[1].card_id == "sndrpihifiberry"
    assert devices[1].hardware_address == "hw:1,0"
    assert devices[1].device_id == (
        "HiFiBerry DAC+ Pro HiFi pcm512x-hifi-0"
    )


def test_start_opens_persistent_raw_pcm_process() -> None:
    driver, _, commands = create_driver()

    driver.start()

    assert commands == [[
        "/usr/bin/aplay",
        "--quiet",
        "--device",
        "hw:1,0",
        "--file-type",
        "raw",
        "--format",
        "S32_LE",
        "--rate",
        "48000",
        "--channels",
        "2",
    ]]
    status = driver.status()
    assert status.state.value == "running"
    assert status.details["streaming"] is True


def test_start_is_idempotent_while_process_runs() -> None:
    driver, _, commands = create_driver()

    driver.start()
    driver.start()

    assert len(commands) == 1


def test_write_sends_pcm_bytes_and_updates_counter() -> None:
    driver, process, _ = create_driver()
    driver.start()

    pcm = b"\x00\x01\x02\x03" * 32
    written = driver.write(pcm)

    assert written == len(pcm)
    assert process.stdin.getvalue() == pcm
    assert driver.status().details["bytes_written"] == len(pcm)


def test_write_rejects_data_before_start() -> None:
    driver, _, _ = create_driver()

    with pytest.raises(AlsaOutputError, match="nicht gestartet"):
        driver.write(b"\x00\x00")


def test_write_rejects_non_bytes() -> None:
    driver, _, _ = create_driver()
    driver.start()

    with pytest.raises(TypeError, match="bytes"):
        driver.write(bytearray(b"\x00"))  # type: ignore[arg-type]


def test_write_detects_terminated_process() -> None:
    process = FakeProcess()
    driver, _, _ = create_driver(process=process)
    driver.start()
    process.exit_code = 1

    with pytest.raises(AlsaOutputError, match="Exit-Code 1"):
        driver.write(b"\x00\x00")

    assert driver.status().state.value == "error"


def test_stop_closes_and_terminates_process() -> None:
    driver, process, _ = create_driver()
    driver.start()

    driver.stop()

    assert process.stdin.closed is True
    assert process.terminated is True
    assert driver.status().state.value == "stopped"
    assert driver.status().details["streaming"] is False


def test_start_rejects_process_without_stdin() -> None:
    process = FakeProcess()
    process.stdin = None
    driver, _, _ = create_driver(process=process)

    with pytest.raises(AlsaOutputError, match="keinen PCM-Eingang"):
        driver.start()


def test_start_rejects_immediately_failed_process() -> None:
    driver, _, _ = create_driver(process=FakeProcess(exit_code=2))

    with pytest.raises(AlsaOutputError, match="Exit-Code 2"):
        driver.start()


def test_start_rejects_unknown_hardware_device() -> None:
    driver, _, _ = create_driver(device="hw:9,9")

    with pytest.raises(AlsaOutputError, match="nicht gefunden"):
        driver.start()


def test_start_rejects_unsupported_pcm_format() -> None:
    driver, _, _ = create_driver(audio_format="U8")

    with pytest.raises(AlsaOutputError, match="nicht unterstützt"):
        driver.start()


def test_start_rejects_non_linux_platform() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(driver="alsa", device="default"),
        platform_name="darwin",
    )

    with pytest.raises(AlsaOutputError, match="nur auf Linux"):
        driver.start()


def test_start_rejects_missing_aplay() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(driver="alsa", device="default"),
        platform_name="linux",
        executable_finder=lambda _: None,
    )

    with pytest.raises(AlsaOutputError, match="aplay"):
        driver.start()
