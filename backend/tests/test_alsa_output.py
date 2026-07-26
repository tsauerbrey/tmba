from __future__ import annotations

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

USB_APLAY_OUTPUT = """\
card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""

MULTI_DEVICE_OUTPUT = """\
card 3: HDMI [vc4-hdmi-0], device 0: MAI PCM i2s-hifi-0 [MAI PCM i2s-hifi-0]
card 3: HDMI [vc4-hdmi-0], device 1: MAI PCM i2s-hifi-0 [MAI PCM i2s-hifi-0]
"""


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


def test_parse_aplay_device_list() -> None:
    devices = AlsaOutputDriver.parse_device_list(
        APLAY_OUTPUT
    )

    assert len(devices) == 2
    assert devices[0].hardware_address == "hw:0,0"
    assert devices[1].card_id == "sndrpihifiberry"
    assert devices[1].hardware_address == "hw:1,0"


def test_parse_preserves_device_names_with_spaces() -> None:
    devices = AlsaOutputDriver.parse_device_list(
        APLAY_OUTPUT
    )

    assert devices[1].device_id == (
        "HiFiBerry DAC+ Pro HiFi pcm512x-hifi-0"
    )
    assert devices[1].device_name == (
        "HiFiBerry DAC+ Pro HiFi pcm512x-hifi-0"
    )


def test_parse_usb_audio_device() -> None:
    devices = AlsaOutputDriver.parse_device_list(
        USB_APLAY_OUTPUT
    )

    assert len(devices) == 1
    assert devices[0].card_name == "USB Audio Device"
    assert devices[0].device_id == "USB Audio"
    assert devices[0].hardware_address == "hw:2,0"


def test_parse_multiple_devices_on_same_card() -> None:
    devices = AlsaOutputDriver.parse_device_list(
        MULTI_DEVICE_OUTPUT
    )

    assert len(devices) == 2
    assert [
        device.hardware_address
        for device in devices
    ] == ["hw:3,0", "hw:3,1"]


def test_parse_ignores_headers_and_subdevice_lines() -> None:
    output = (
        "**** List of PLAYBACK Hardware Devices ****\n"
        + USB_APLAY_OUTPUT
    )

    devices = AlsaOutputDriver.parse_device_list(output)

    assert len(devices) == 1


def test_discover_devices_uses_aplay() -> None:
    commands: list[list[str]] = []

    def runner(command):
        commands.append(list(command))
        return result()

    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="hw:1,0",
        ),
        command_runner=runner,
        platform_name="linux",
        executable_finder=lambda _: "/usr/bin/aplay",
    )

    devices = driver.discover_devices()

    assert commands == [["/usr/bin/aplay", "-l"]]
    assert len(devices) == 2


def test_start_prepares_known_alsa_device() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="hw:1,0",
        ),
        command_runner=lambda _: result(),
        platform_name="linux",
        executable_finder=lambda _: "/usr/bin/aplay",
    )

    driver.start()
    status = driver.status()

    assert status.state.value == "ready"
    assert status.details["device_count"] == 2
    assert status.details["streaming"] is False
    assert status.details["simulation"] is False


def test_start_rejects_non_linux_platform() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="default",
        ),
        platform_name="darwin",
    )

    with pytest.raises(
        AlsaOutputError,
        match="nur auf Linux",
    ):
        driver.start()

    assert driver.status().state.value == "error"


def test_start_rejects_missing_aplay() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="default",
        ),
        platform_name="linux",
        executable_finder=lambda _: None,
    )

    with pytest.raises(
        AlsaOutputError,
        match="aplay",
    ):
        driver.start()


def test_start_rejects_unknown_hardware_device() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="hw:9,9",
        ),
        command_runner=lambda _: result(),
        platform_name="linux",
        executable_finder=lambda _: "/usr/bin/aplay",
    )

    with pytest.raises(
        AlsaOutputError,
        match="nicht gefunden",
    ):
        driver.start()


def test_discovery_reports_aplay_error() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="default",
        ),
        command_runner=lambda _: result(
            returncode=1,
            stdout="",
            stderr="no soundcards found",
        ),
        platform_name="linux",
        executable_finder=lambda _: "/usr/bin/aplay",
    )

    with pytest.raises(
        AlsaOutputError,
        match="no soundcards found",
    ):
        driver.discover_devices()


def test_stop_resets_driver_state() -> None:
    driver = AlsaOutputDriver(
        OutputConfig(
            driver="alsa",
            device="default",
        ),
        command_runner=lambda _: result(),
        platform_name="linux",
        executable_finder=lambda _: "/usr/bin/aplay",
    )

    driver.start()
    driver.stop()

    assert driver.status().state.value == "stopped"
