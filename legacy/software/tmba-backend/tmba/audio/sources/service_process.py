"""Testable service-control boundary for systemd-managed audio sources."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Callable, Protocol, Sequence


class ServiceRuntimeState(str, Enum):
    UNKNOWN = "unknown"
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ServiceSnapshot:
    name: str
    state: ServiceRuntimeState
    sub_state: str = "unknown"
    main_pid: int | None = None
    error: str | None = None

    @property
    def running(self) -> bool:
        return self.state is ServiceRuntimeState.ACTIVE

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["state"] = self.state.value
        result["running"] = self.running
        return result


class ServiceControlError(RuntimeError):
    """Raised when a service manager operation fails."""


class ServiceController(Protocol):
    def inspect(self, service_name: str) -> ServiceSnapshot: ...
    def start(self, service_name: str) -> ServiceSnapshot: ...
    def stop(self, service_name: str) -> ServiceSnapshot: ...
    def restart(self, service_name: str) -> ServiceSnapshot: ...


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class SystemdServiceController:
    """Small systemctl adapter with dependency injection for unit tests."""

    _SHOW_PROPERTIES = "ActiveState,SubState,MainPID"

    def __init__(
        self,
        *,
        command_runner: CommandRunner | None = None,
        executable_finder: Callable[[str], str | None] | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        self._runner = command_runner or self._run
        self._finder = executable_finder or shutil.which
        self._timeout_seconds = float(timeout_seconds)

    def inspect(self, service_name: str) -> ServiceSnapshot:
        name = self._normalize_name(service_name)
        result = self._execute([
            "show", name, "--no-page",
            f"--property={self._SHOW_PROPERTIES}",
        ], allow_inactive=True)
        values: dict[str, str] = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                values[key.strip()] = value.strip()
        active_state = values.get("ActiveState", "unknown")
        try:
            state = ServiceRuntimeState(active_state)
        except ValueError:
            state = ServiceRuntimeState.UNKNOWN
        pid_text = values.get("MainPID", "0")
        main_pid = int(pid_text) if pid_text.isdigit() and int(pid_text) > 0 else None
        return ServiceSnapshot(
            name=name,
            state=state,
            sub_state=values.get("SubState", "unknown"),
            main_pid=main_pid,
        )

    def start(self, service_name: str) -> ServiceSnapshot:
        name = self._normalize_name(service_name)
        self._execute(["start", name])
        return self.inspect(name)

    def stop(self, service_name: str) -> ServiceSnapshot:
        name = self._normalize_name(service_name)
        self._execute(["stop", name], allow_inactive=True)
        return self.inspect(name)

    def restart(self, service_name: str) -> ServiceSnapshot:
        name = self._normalize_name(service_name)
        self._execute(["restart", name])
        return self.inspect(name)

    def _execute(
        self,
        arguments: Sequence[str],
        *,
        allow_inactive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        executable = self._finder("systemctl")
        if executable is None:
            raise ServiceControlError("systemctl wurde nicht gefunden.")
        result = self._runner([executable, *arguments])
        if result.returncode != 0 and not allow_inactive:
            message = (result.stderr or result.stdout).strip()
            raise ServiceControlError(
                f"systemctl {' '.join(arguments)} ist fehlgeschlagen"
                + (f": {message}" if message else ".")
            )
        return result

    def _run(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                list(command), check=False, capture_output=True, text=True,
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise ServiceControlError(
                f"Dienstbefehl überschritt {self._timeout_seconds:g} Sekunden."
            ) from error

    @staticmethod
    def _normalize_name(service_name: str) -> str:
        name = str(service_name).strip()
        if not name or any(character.isspace() for character in name):
            raise ValueError("Ungültiger systemd-Dienstname.")
        return name if "." in name else f"{name}.service"
