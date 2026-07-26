from __future__ import annotations

import subprocess

import pytest

from tmba.audio.sources.service_process import (
    ServiceControlError, ServiceRuntimeState, SystemdServiceController,
)


def completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def test_inspect_parses_systemd_properties():
    commands = []
    controller = SystemdServiceController(
        command_runner=lambda command: (
            commands.append(list(command)) or completed(
                "ActiveState=active\nSubState=running\nMainPID=1234\n"
            )
        ),
        executable_finder=lambda _: "/bin/systemctl",
    )
    snapshot = controller.inspect("shairport-sync")
    assert snapshot.state is ServiceRuntimeState.ACTIVE
    assert snapshot.sub_state == "running"
    assert snapshot.main_pid == 1234
    assert snapshot.running is True
    assert commands[0][0:3] == ["/bin/systemctl", "show", "shairport-sync.service"]


def test_start_runs_command_then_inspects():
    commands = []
    def runner(command):
        commands.append(list(command))
        if "show" in command:
            return completed("ActiveState=active\nSubState=running\nMainPID=9\n")
        return completed()
    snapshot = SystemdServiceController(
        command_runner=runner,
        executable_finder=lambda _: "/bin/systemctl",
    ).start("demo.service")
    assert snapshot.running
    assert commands[0] == ["/bin/systemctl", "start", "demo.service"]


def test_missing_systemctl_is_reported():
    controller = SystemdServiceController(executable_finder=lambda _: None)
    with pytest.raises(ServiceControlError, match="nicht gefunden"):
        controller.inspect("demo")


def test_failed_start_includes_service_manager_message():
    controller = SystemdServiceController(
        command_runner=lambda _: completed(stderr="access denied", returncode=1),
        executable_finder=lambda _: "/bin/systemctl",
    )
    with pytest.raises(ServiceControlError, match="access denied"):
        controller.start("demo")


def test_invalid_service_name_is_rejected():
    controller = SystemdServiceController()
    with pytest.raises(ValueError, match="Ungültiger"):
        controller.inspect("bad service")
