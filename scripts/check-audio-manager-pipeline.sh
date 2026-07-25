#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.6.1-B – AudioManager/Pipeline-Prüfung"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "1. AudioManager-Tests"
PYTHONPATH=. python -m pytest -q \
  tests/test_audio_manager.py \
  tests/test_audio_manager_pipeline.py

echo
echo "2. AudioPipeline-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_pipeline.py

echo
echo "3. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "AudioManager/Pipeline-Prüfung erfolgreich."
