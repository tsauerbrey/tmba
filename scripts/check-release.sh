#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "TMBA Release-Prüfung"
echo "Projekt: ${PROJECT_ROOT}"

echo
echo "=== Backend-Tests ==="
cd "${PROJECT_ROOT}/backend"

if [[ ! -d ".venv" ]]; then
  echo "Fehler: backend/.venv wurde nicht gefunden."
  exit 1
fi

source .venv/bin/activate
PYTHONPATH=. python -m pytest -q

echo
echo "=== Frontend-Build ==="
cd "${PROJECT_ROOT}/frontend"

if [[ ! -d "node_modules" ]]; then
  echo "Installiere Frontend-Abhängigkeiten ..."
  npm install
fi

npm run build

echo
echo "=== Git-Status ==="
cd "${PROJECT_ROOT}"
git status --short

echo
echo "Release-Prüfung erfolgreich."
