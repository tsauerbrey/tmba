#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.7.0-B – Source-Arbitration-Prüfung"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "1. Source-Arbitration-Tests"
PYTHONPATH=. python -m pytest -q tests/test_source_arbitration.py

echo
echo "2. AudioEngine-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_engine.py

echo
echo "3. AudioEngine-API-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_engine_api.py

echo
echo "4. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "TMBA v0.7.0-B erfolgreich geprüft."
