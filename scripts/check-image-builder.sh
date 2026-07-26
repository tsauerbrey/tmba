#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PYTHON="$BACKEND_DIR/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "Fehler: Backend-venv fehlt: $PYTHON" >&2; exit 1; }
export PYTHONPATH="$BACKEND_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "TMBA v0.8.1 – Bookworm pi-gen Baseline"
echo
echo "1. Builder-Konfiguration"
"$ROOT_DIR/image-builder/validate.sh"
echo
echo "2. Builder-Tests"
cd "$BACKEND_DIR"
"$PYTHON" -m pytest -q "$ROOT_DIR/image-builder/tests/test_builder.py"
echo
echo "3. Dry-Run"
cd "$ROOT_DIR"
"$ROOT_DIR/image-builder/build.sh" --dry-run
echo
echo "4. Shell-Syntax"
find "$ROOT_DIR/image-builder" -type f \( -name '*.sh' -o -name '*-run-chroot.sh' \) -print0 | xargs -0 -n1 bash -n
echo
echo "5. Vollständige Backend-Tests"
cd "$BACKEND_DIR"
"$PYTHON" -m pytest -q
echo
echo "TMBA v0.8.1 erfolgreich geprüft."
