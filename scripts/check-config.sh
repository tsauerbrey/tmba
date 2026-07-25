#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIRECTORY="$(cd "${SCRIPT_DIRECTORY}/.." && pwd)"
BACKEND_DIRECTORY="${PROJECT_DIRECTORY}/backend"

if [[ ! -d "${BACKEND_DIRECTORY}" ]]; then
  echo "Fehler: Backend-Verzeichnis nicht gefunden: ${BACKEND_DIRECTORY}" >&2
  exit 1
fi

cd "${BACKEND_DIRECTORY}"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  echo "Fehler: Python 3 wurde nicht gefunden." >&2
  exit 1
fi

"${PYTHON}" - <<'PYTHON'
from tmba.core.config import get_settings

settings = get_settings(reload=True)

print("TMBA-Konfiguration ist gültig.")
print(f"Projekt:       {settings.system.project.name}")
print(f"Version:       {settings.system.project.version}")
print(
    "Display:       "
    f"{settings.display.display.width} x "
    f"{settings.display.display.height}, "
    f"Rotation {settings.display.display.rotation}°"
)
print(f"Startlautstärke: {settings.audio.volume.startup} %")
print(f"DSP:           {'aktiv' if settings.dsp.enabled else 'inaktiv'}")
print(
    "WebUI:         "
    f"http://{settings.network.webui.local_hostname}:"
    f"{settings.network.webui.port}"
)
print(f"Konfigurationsordner: {settings.config_directory}")
PYTHON
