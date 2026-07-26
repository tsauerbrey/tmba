#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then echo "Fehler: backend/.venv fehlt."; exit 1; fi
source .venv/bin/activate
export PYTHONPATH=.
echo "TMBA v0.7.2-A – ServiceSource- und AirPlay-Adapter-Prüfung"
echo
echo "1. systemd-ServiceController"
python -m pytest -q tests/test_service_process.py
echo
echo "2. ServiceSource"
python -m pytest -q tests/test_service_source.py
echo
echo "3. AirPlay-Adapter"
python -m pytest -q tests/test_airplay_source.py
echo
echo "4. Vollständige Backend-Tests"
python -m pytest -q
echo
echo "TMBA v0.7.2-A erfolgreich geprüft."
