#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

if [[ ! -d "${BACKEND_DIR}" ]]; then
  BACKEND_DIR="${PROJECT_ROOT}"
fi

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: ${BACKEND_DIR}/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "TMBA v0.7.1-B – DummySource- und PCM-Prüfung"
echo
echo "1. PCM-Generator"
PYTHONPATH=. python -m pytest -q tests/test_pcm_generator.py
echo
echo "2. DummySource"
PYTHONPATH=. python -m pytest -q tests/test_dummy_source.py
echo
echo "3. PCM-Datenfluss"
PYTHONPATH=. python -m pytest -q tests/test_pcm_pipeline_flow.py
echo
echo "4. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q
echo
echo "TMBA v0.7.1-B erfolgreich geprüft."
