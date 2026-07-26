#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.6.2-B – ALSA-PCM-Streaming-Prüfung"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "1. ALSA-PCM-Streaming-Tests"
PYTHONPATH=. python -m pytest -q tests/test_alsa_output.py

echo
echo "2. OutputDriver-Factory und AudioPipeline"
PYTHONPATH=. python -m pytest -q \
  tests/test_output_factory.py \
  tests/test_audio_pipeline.py \
  tests/test_audio_manager_pipeline.py

echo
echo "3. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "TMBA v0.6.2-B erfolgreich geprüft."
