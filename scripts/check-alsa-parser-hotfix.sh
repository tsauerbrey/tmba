#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.6.2-A1 – ALSA-Parser-Hotfix"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "1. ALSA-Parser- und Driver-Tests"
PYTHONPATH=. python -m pytest -q \
  tests/test_alsa_output.py

echo
echo "2. OutputDriver-Factory"
PYTHONPATH=. python -m pytest -q \
  tests/test_output_factory.py

echo
echo "3. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "TMBA v0.6.2-A1 erfolgreich geprüft."
