#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.7.0-A – AudioEngine-Prüfung"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "1. AudioEngine-Unit-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_engine.py

echo
echo "2. AudioEngine-REST-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_engine_api.py

echo
echo "3. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "TMBA v0.7.0-A erfolgreich geprüft."
