#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.6.1-C – Pipeline-REST-API-Prüfung"
cd "${PROJECT_ROOT}"

if tail -n 8 backend/tmba/audio/manager.py | grep -q '^register_default_sources()$'; then
  echo "Fehler: manager.py registriert Quellen noch beim Import."
  echo "Bitte zuerst ausführen: python3 scripts/move-default-source-registration.py"
  exit 1
fi
if ! grep -q '^register_default_sources()$' backend/tmba/main.py; then
  echo "Fehler: main.py registriert die Standardquellen nicht."
  exit 1
fi

cd "${BACKEND_DIR}"
if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi
source .venv/bin/activate

echo "1. Neue Pipeline-API-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_pipeline_api.py

echo "2. AudioManager- und Pipeline-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_manager.py tests/test_audio_manager_pipeline.py tests/test_audio_pipeline.py

echo "3. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo "Pipeline-REST-API-Prüfung erfolgreich."
