#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PYTHON="$BACKEND_DIR/.venv/bin/python"

[[ -x "$PYTHON" ]] || {
    echo "Fehler: Backend-venv fehlt: $PYTHON" >&2
    exit 1
}

export PYTHONPATH="$BACKEND_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "TMBA v0.7.2-B – AirPlay-Laufzeitintegration"
echo

cd "$BACKEND_DIR"

echo "1. AirPlay-Konfiguration und Laufzeitdiagnose"
"$PYTHON" -m pytest -q tests/test_airplay_runtime.py

echo
echo "2. AirPlaySource"
"$PYTHON" -m pytest -q tests/test_airplay_source.py

echo
echo "3. Vollständige Backend-Tests"
"$PYTHON" -m pytest -q

echo
echo "4. Deployment-Dateien"
bash -n "$ROOT_DIR/scripts/install-airplay-runtime.sh"
test -f "$ROOT_DIR/config/shairport-sync/tmba.conf.template"
test -f "$ROOT_DIR/config/shairport-sync/tmba-override.conf"

echo
echo "TMBA v0.7.2-B erfolgreich geprüft."
