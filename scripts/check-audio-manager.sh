#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"

echo "Prüfe TMBA AudioManager unter ${BASE_URL} ..."

echo
echo "=== AUDIOSTATUS ==="
curl --fail --silent --show-error \
  "${BASE_URL}/audio/status"
echo

echo
echo "=== QUELLE WEBRADIO AUSWÄHLEN ==="
curl --fail --silent --show-error \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"source":"webradio"}' \
  "${BASE_URL}/audio/source"
echo

echo
echo "=== LAUTSTÄRKE 42 ==="
curl --fail --silent --show-error \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"volume":42}' \
  "${BASE_URL}/audio/volume"
echo

echo
echo "=== QUELLE STOPPEN / NONE ==="
curl --fail --silent --show-error \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"source":"none"}' \
  "${BASE_URL}/audio/source"
echo

echo
echo "AudioManager antwortet korrekt."
