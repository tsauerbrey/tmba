from __future__ import annotations

import subprocess

import pytest

from tmba.audio.sources.airplay_runtime import (
    AirPlayRuntimeConfig,
    AirPlayRuntimeInspector,
    write_airplay_config,
)


def completed(command, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def test_runtime_config_renders_receiver_and_hifiberry_alsa_settings():
    config = AirPlayRuntimeConfig(receiver_name="TMBA Wohnzimmer")
    rendered = config.render()
    assert 'name = "TMBA Wohnzimmer";' in rendered
    assert 'output_backend = "alsa";' in rendered
    assert 'output_device = "hw:sndrpihifiberry";' in rendered
    assert 'mixer_control_name = "Digital";' in rendered
    assert 'mixer_device = "hw:sndrpihifiberry";' in rendered


def test_runtime_config_escapes_quotes_and_backslashes():
    rendered = AirPlayRuntimeConfig(receiver_name='TMBA "Mobil" \\').render()
    assert 'TMBA \\"Mobil\\" \\\\' in rendered


@pytest.mark.parametrize("field", ["receiver_name", "output_device", "service_name", "config_path"])
def test_runtime_config_rejects_empty_required_values(field):
    values = {field: "   "}
    with pytest.raises(ValueError):
        AirPlayRuntimeConfig(**values)


def test_write_airplay_config_creates_parent_and_replaces_file(tmp_path):
    destination = tmp_path / "etc" / "shairport-sync.conf"
    result = write_airplay_config(
        destination,
        AirPlayRuntimeConfig(receiver_name="TMBA Test"),
    )
    assert result == destination
    assert destination.is_file()
    assert 'name = "TMBA Test";' in destination.read_text(encoding="utf-8")
    assert not destination.with_suffix(".conf.tmp").exists()


def test_runtime_inspector_reports_ready_host():
    def finder(name):
        return f"/usr/bin/{name}"

    def runner(command):
        if command[-1] == "-L":
            return completed(command, stdout="null\nhw:sndrpihifiberry\n")
        if "LoadState" in command:
            return completed(command, stdout="loaded\n")
        return completed(command)

    inspector = AirPlayRuntimeInspector(
        executable_finder=finder,
        command_runner=runner,
        path_exists=lambda path: path == "/etc/shairport-sync.conf",
    )
    report = inspector.inspect(AirPlayRuntimeConfig())
    assert report.ready is True
    assert report.binary_found is True
    assert report.service_available is True
    assert report.avahi_active is True
    assert report.alsa_device_found is True
    assert report.error is None


def test_runtime_inspector_lists_missing_prerequisites():
    inspector = AirPlayRuntimeInspector(
        executable_finder=lambda name: None,
        command_runner=lambda command: completed(command, returncode=1),
        path_exists=lambda path: False,
    )
    report = inspector.inspect(AirPlayRuntimeConfig())
    assert report.ready is False
    assert report.binary_found is False
    assert report.config_found is False
    assert report.service_available is False
    assert report.avahi_active is False
    assert report.alsa_device_found is False
    assert "shairport-sync" in report.error
    assert "hw:sndrpihifiberry" in report.error


def test_runtime_inspector_accepts_card_name_from_aplay_listing():
    def finder(name):
        return f"/usr/bin/{name}"

    def runner(command):
        if command[-1] == "-L":
            return completed(command, stdout="sysdefault:CARD=sndrpihifiberry\n")
        return completed(command, stdout="loaded\n")

    inspector = AirPlayRuntimeInspector(
        executable_finder=finder,
        command_runner=runner,
        path_exists=lambda path: True,
    )
    report = inspector.inspect(AirPlayRuntimeConfig())
    assert report.alsa_device_found is True
