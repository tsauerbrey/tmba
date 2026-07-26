#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PYTHON="$BACKEND_DIR/.venv/bin/python"

[[ -x "$PYTHON" ]] || { echo "Fehler: Backend-venv fehlt: $PYTHON" >&2; exit 1; }
export PYTHONPATH="$BACKEND_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "TMBA v0.7.3-A – Developer Image Builder"
echo

echo "1. Builder-Konfiguration"
"$ROOT_DIR/image-builder/validate.sh"

echo
echo "2. Builder-Tests"
cd "$ROOT_DIR"
"$PYTHON" -m pytest -q image-builder/tests

echo
echo "3. Dry-Run"
"$ROOT_DIR/image-builder/build.sh" --dry-run

echo
echo "4. Vollständige Backend-Tests"
cd "$BACKEND_DIR"
"$PYTHON" -m pytest -q

echo
echo "TMBA v0.7.3-A erfolgreich geprüft."
