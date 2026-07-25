#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"

echo "Prüfe TMBA-Netzwerkdienst unter ${BASE_URL} ..."

echo
echo "=== STATUS ==="
curl --fail --silent --show-error \
  "${BASE_URL}/network/status"
echo

echo
echo "=== INTERFACES ==="
curl --fail --silent --show-error \
  "${BASE_URL}/network/interfaces"
echo

echo
echo "=== WLAN-SCAN ==="
curl --fail --silent --show-error \
  "${BASE_URL}/network/wifi/scan"
echo

echo
echo "=== GESPEICHERTE WLAN-VERBINDUNGEN ==="
curl --fail --silent --show-error \
  "${BASE_URL}/network/wifi/saved"
echo

echo
echo "=== SICHERER CONNECT-TEST ==="
curl --fail --silent --show-error \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"ssid":"TMBA-Testnetz","password":"nur-ein-test"}' \
  "${BASE_URL}/network/wifi/connect"
echo

echo
echo "Hinweis: Auf macOS wird keine Verbindung verändert."
echo "Auf dem Raspberry bitte echte WLAN-Zugangsdaten ausschließlich"
echo "über die GUI oder einen gezielten API-Aufruf verwenden."

echo
echo "TMBA-Netzwerkdienst antwortet korrekt."
