#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.7.1-A – AudioSource-API-Prüfung"
echo

if [[ ! -d "${BACKEND_DIR}/.venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

cd "${BACKEND_DIR}"
source .venv/bin/activate

echo "1. AudioSource-API-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_source_api.py

echo
echo "2. Source-Arbitration-Tests"
PYTHONPATH=. python -m pytest -q tests/test_source_arbitration.py

echo
echo "3. AudioEngine-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_engine.py

echo
echo "4. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "TMBA v0.7.1-A erfolgreich geprüft."
