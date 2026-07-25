#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${PROJECT_ROOT}/frontend"

echo "Prüfe TMBA-Frontend ..."
echo

echo "=== NODE ==="
node --version

echo
echo "=== NPM ==="
npm --version

echo
echo "=== VUE-BUILD ==="
npm run build

echo
echo "Frontend erfolgreich gebaut."
echo "Ausgabe: ${PROJECT_ROOT}/frontend/dist"
