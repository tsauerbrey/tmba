#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"

echo "Prüfe TMBA-Systemdienst unter ${BASE_URL} ..."

echo
echo "=== HEALTH ==="
curl --fail --silent --show-error \
  "${BASE_URL}/system/health"
echo

echo
echo "=== SYSTEMINFO ==="
curl --fail --silent --show-error \
  "${BASE_URL}/system/info"
echo

echo
echo "TMBA-Systemdienst antwortet korrekt."
