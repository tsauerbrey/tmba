#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$ROOT_DIR/.." && pwd)"
CONFIG_FILE="$ROOT_DIR/config/image.env"

fail() { echo "Fehler: $*" >&2; exit 1; }
require_file() { [[ -f "$1" ]] || fail "Datei fehlt: ${1#$REPO_DIR/}"; }
require_dir() { [[ -d "$1" ]] || fail "Verzeichnis fehlt: ${1#$REPO_DIR/}"; }

require_file "$REPO_DIR/VERSION"
require_file "$CONFIG_FILE"
require_file "$ROOT_DIR/config/services.txt"
require_file "$ROOT_DIR/packages/base.txt"
require_file "$ROOT_DIR/packages/audio.txt"
require_file "$ROOT_DIR/packages/development.txt"
require_file "$ROOT_DIR/overlays/rootfs/etc/systemd/system/tmba-backend.service"

for stage in 00-base 10-audio 20-network 30-tmba 40-finalize; do
  require_dir "$ROOT_DIR/stages/$stage"
done

# shellcheck disable=SC1090
source "$CONFIG_FILE"

[[ "$TMBA_IMAGE_VERSION" == "$(tr -d '[:space:]' < "$REPO_DIR/VERSION")" ]] || \
  fail "VERSION und TMBA_IMAGE_VERSION stimmen nicht überein"
[[ "$TMBA_TARGET_BOARD" == "raspberry-pi-4" ]] || fail "Unerwartetes Zielboard"
[[ "$TMBA_TARGET_ARCH" == "arm64" ]] || fail "Unerwartete Zielarchitektur"
[[ "$TMBA_BASE_OS" == "raspberry-pi-os-lite" ]] || fail "Unerwartetes Basisbetriebssystem"
[[ "$TMBA_ENABLE_SSH" == "1" ]] || fail "SSH muss für das Developer Image aktiviert sein"

while IFS= read -r file; do
  awk 'NF && $1 !~ /^#/ { if ($1 !~ /^[a-z0-9][a-z0-9+.-]*$/) exit 1 }' "$file" || \
    fail "Ungültiger Paketname in ${file#$REPO_DIR/}"
done < <(find "$ROOT_DIR/packages" -type f -name '*.txt' | sort)

awk 'NF && $1 !~ /^#/ { if ($1 !~ /^[A-Za-z0-9@_.:-]+\.service$/) exit 1 }' \
  "$ROOT_DIR/config/services.txt" || fail "Ungültiger Dienstname"

bash -n "$ROOT_DIR/build.sh"
bash -n "$ROOT_DIR/validate.sh"

echo "TMBA Image Builder-Konfiguration ist gültig."
