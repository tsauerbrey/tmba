"""Central configuration loader for TMBA.

The loader reads YAML files from the repository-level ``config`` directory.
Configuration values can be accessed as dictionaries or by attribute notation:

    settings.system.project.name
    settings.audio.volume.startup

The module does not modify any existing TMBA service. It is a foundation for
later milestones.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Iterator, Mapping

import yaml


class ConfigError(RuntimeError):
    """Raised when TMBA configuration cannot be loaded or validated."""


class ConfigNode(Mapping[str, Any]):
    """Read-only mapping with convenient attribute access."""

    def __init__(self, data: Mapping[str, Any], *, path: str = "config") -> None:
        self._path = path
        self._data: dict[str, Any] = {
            key: self._convert(value, f"{path}.{key}") for key, value in data.items()
        }

    @classmethod
    def _convert(cls, value: Any, path: str) -> Any:
        if isinstance(value, Mapping):
            return cls(value, path=path)
        if isinstance(value, list):
            return [cls._convert(item, f"{path}[]") for item in value]
        return value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError(
                f"Configuration value '{self._path}.{name}' does not exist."
            ) from exc

    def get_path(self, dotted_path: str, default: Any = None) -> Any:
        """Return a nested value from a dotted path."""

        current: Any = self
        for part in dotted_path.split("."):
            if isinstance(current, ConfigNode) and part in current:
                current = current[part]
            else:
                return default
        return current

    def to_dict(self) -> dict[str, Any]:
        """Return a recursively converted plain dictionary."""

        result: dict[str, Any] = {}
        for key, value in self._data.items():
            if isinstance(value, ConfigNode):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, ConfigNode) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def __repr__(self) -> str:
        return f"ConfigNode(path={self._path!r}, keys={list(self._data)})"


@dataclass(frozen=True)
class TMBASettings:
    """Container for all TMBA configuration sections."""

    system: ConfigNode
    audio: ConfigNode
    display: ConfigNode
    network: ConfigNode
    dsp: ConfigNode
    config_directory: Path


class ConfigLoader:
    """Load and validate TMBA YAML configuration files."""

    FILES = ("system", "audio", "display", "network", "dsp")

    def __init__(self, config_directory: Path | str | None = None) -> None:
        self.config_directory = (
            Path(config_directory).expanduser().resolve()
            if config_directory is not None
            else self._find_default_config_directory()
        )

    @staticmethod
    def _find_default_config_directory() -> Path:
        current_file = Path(__file__).resolve()

        for parent in current_file.parents:
            candidate = parent / "config"
            if candidate.is_dir():
                return candidate

        raise ConfigError(
            "TMBA configuration directory was not found. "
            "Expected a repository-level directory named 'config'."
        )

    def load(self) -> TMBASettings:
        loaded: dict[str, ConfigNode] = {}

        for section_name in self.FILES:
            file_path = self.config_directory / f"{section_name}.yaml"
            loaded[section_name] = ConfigNode(
                self._load_yaml(file_path),
                path=section_name,
            )

        settings = TMBASettings(
            system=loaded["system"],
            audio=loaded["audio"],
            display=loaded["display"],
            network=loaded["network"],
            dsp=loaded["dsp"],
            config_directory=self.config_directory,
        )
        self._validate(settings)
        return settings

    @staticmethod
    def _load_yaml(file_path: Path) -> dict[str, Any]:
        if not file_path.is_file():
            raise ConfigError(f"Required configuration file is missing: {file_path}")

        try:
            with file_path.open("r", encoding="utf-8") as handle:
                content = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {file_path}: {exc}") from exc
        except OSError as exc:
            raise ConfigError(f"Could not read {file_path}: {exc}") from exc

        if content is None:
            return {}

        if not isinstance(content, dict):
            raise ConfigError(
                f"The root element in {file_path} must be a YAML mapping."
            )

        return content

    @staticmethod
    def _validate(settings: TMBASettings) -> None:
        width = settings.display.get_path("display.width")
        height = settings.display.get_path("display.height")
        rotation = settings.display.get_path("display.rotation")
        startup_volume = settings.audio.get_path("volume.startup")
        maximum_volume = settings.audio.get_path("volume.maximum")
        minimum_volume = settings.audio.get_path("volume.minimum")
        webui_port = settings.network.get_path("webui.port")

        if not isinstance(width, int) or width <= 0:
            raise ConfigError("display.display.width must be a positive integer.")

        if not isinstance(height, int) or height <= 0:
            raise ConfigError("display.display.height must be a positive integer.")

        if rotation not in {0, 90, 180, 270}:
            raise ConfigError("display.display.rotation must be 0, 90, 180 or 270.")

        for label, value in (
            ("audio.volume.minimum", minimum_volume),
            ("audio.volume.startup", startup_volume),
            ("audio.volume.maximum", maximum_volume),
        ):
            if not isinstance(value, int) or not 0 <= value <= 100:
                raise ConfigError(f"{label} must be an integer from 0 to 100.")

        if not minimum_volume <= startup_volume <= maximum_volume:
            raise ConfigError(
                "audio volume values must satisfy minimum <= startup <= maximum."
            )

        if not isinstance(webui_port, int) or not 1 <= webui_port <= 65535:
            raise ConfigError("network.webui.port must be an integer from 1 to 65535.")


_settings_lock = RLock()
_settings: TMBASettings | None = None


def get_settings(*, reload: bool = False) -> TMBASettings:
    """Return the process-wide TMBA settings instance."""

    global _settings

    with _settings_lock:
        if _settings is None or reload:
            _settings = ConfigLoader().load()
        return _settings


settings = get_settings()
