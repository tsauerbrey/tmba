#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "TMBA v0.6.1-D – Release-Abschlussprüfung"
echo

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate

echo "1. Pipeline-Vertragstests"
PYTHONPATH=. python -m pytest -q \
  tests/test_audio_pipeline_contract.py

echo
echo "2. AudioManager, Pipeline und REST API"
PYTHONPATH=. python -m pytest -q \
  tests/test_audio_manager.py \
  tests/test_audio_manager_pipeline.py \
  tests/test_audio_pipeline.py \
  tests/test_audio_pipeline_api.py \
  tests/test_audio_pipeline_contract.py

echo
echo "3. Vollständige Backend-Tests"
PYTHONPATH=. python -m pytest -q

echo
echo "4. OpenAPI-Dokument exportieren"
cd "${PROJECT_ROOT}"
python3 scripts/export-openapi.py

echo
echo "5. Exportiertes OpenAPI-Dokument prüfen"
python3 -m json.tool docs/api/openapi.json >/dev/null

if ! grep -q '"/audio/pipeline"' docs/api/openapi.json; then
  echo "Fehler: /audio/pipeline fehlt in docs/api/openapi.json."
  exit 1
fi

echo
echo "TMBA v0.6.1 ist releasebereit."
