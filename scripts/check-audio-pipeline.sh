#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.6.1-A – AudioPipeline-Prüfung"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  echo "Bitte zuerst die virtuelle Python-Umgebung aktivieren oder anlegen."
  exit 1
fi

source .venv/bin/activate

echo "1. AudioPipeline-Tests"
PYTHONPATH=. python -m pytest -q tests/test_audio_pipeline.py

echo
echo "2. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "AudioPipeline-Prüfung erfolgreich."
