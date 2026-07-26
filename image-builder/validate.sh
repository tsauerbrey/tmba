#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$ROOT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT_DIR/lib/common.sh"
CONFIG_FILE="$ROOT_DIR/config/image.env"

require_file() { [[ -f "$1" ]] || fail "Datei fehlt: ${1#$REPO_DIR/}"; }
require_dir() { [[ -d "$1" ]] || fail "Verzeichnis fehlt: ${1#$REPO_DIR/}"; }

require_file "$REPO_DIR/VERSION"
require_file "$CONFIG_FILE"
require_file "$ROOT_DIR/config/services.txt"
require_file "$ROOT_DIR/prepare-pigen.sh"
require_file "$ROOT_DIR/preflight.sh"
require_file "$ROOT_DIR/lib/common.sh"
require_file "$ROOT_DIR/pi-gen-stage/EXPORT_IMAGE"
require_file "$ROOT_DIR/pi-gen-stage/00-tmba-packages/00-packages"
require_file "$ROOT_DIR/pi-gen-stage/01-tmba-files/00-run.sh"
require_file "$ROOT_DIR/pi-gen-stage/02-tmba-install/00-run-chroot.sh"
require_file "$ROOT_DIR/pi-gen-stage/03-tmba-hardware/00-run.sh"
require_file "$ROOT_DIR/pi-gen-stage/04-tmba-services/00-run-chroot.sh"
require_file "$ROOT_DIR/pi-gen-stage/05-tmba-finalize/00-run-chroot.sh"
require_file "$ROOT_DIR/overlays/rootfs/etc/systemd/system/tmba-backend.service"

for stage in 00-base 10-audio 20-network 30-tmba 40-finalize; do
  require_dir "$ROOT_DIR/stages/$stage"
done

# shellcheck disable=SC1090
source "$CONFIG_FILE"
[[ "$TMBA_IMAGE_VERSION" == "$(repo_version "$REPO_DIR")" ]] || fail "VERSION und TMBA_IMAGE_VERSION stimmen nicht überein"
[[ "$TMBA_TARGET_BOARD" == "raspberry-pi-4" ]] || fail "Unerwartetes Zielboard"
[[ "$TMBA_TARGET_ARCH" == "arm64" ]] || fail "Unerwartete Zielarchitektur"
[[ "$TMBA_BASE_OS" == "raspberry-pi-os-lite" ]] || fail "Unerwartetes Basisbetriebssystem"
[[ "$TMBA_ENABLE_SSH" == "1" ]] || fail "SSH muss im Developer Image aktiv sein"
[[ "$TMBA_PI_GEN_REPOSITORY" == https://github.com/RPi-Distro/pi-gen.git ]] || fail "Unerwartetes pi-gen-Repository"
[[ -n "$TMBA_PI_GEN_REF" ]] || fail "TMBA_PI_GEN_REF fehlt"
[[ "$TMBA_PI_GEN_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail "TMBA_PI_GEN_COMMIT muss ein vollständiger Git-Commit sein"
(( TMBA_MIN_FREE_GIB >= 35 )) || fail "Mindestplatz muss mindestens 35 GiB betragen"
(( TMBA_MIN_DOCKER_MEMORY_GIB >= 8 )) || fail "Docker-RAM muss mindestens 8 GiB betragen"
(( TMBA_MIN_DOCKER_CPUS >= 4 )) || fail "Docker-CPU-Anzahl muss mindestens 4 betragen"
[[ "$TMBA_DOCKER_PLATFORM" == "linux/arm64" ]] || fail "Unerwartete Docker-Plattform"

while IFS= read -r file; do
  awk 'NF && $1 !~ /^#/ { if ($1 !~ /^[a-z0-9][a-z0-9+.-]*$/) exit 1 }' "$file" || fail "Ungültiger Paketname in ${file#$REPO_DIR/}"
done < <(find "$ROOT_DIR/packages" "$ROOT_DIR/pi-gen-stage" -type f \( -name '*.txt' -o -name '00-packages' \) | sort)

for script in \
  "$ROOT_DIR/build.sh" \
  "$ROOT_DIR/prepare-pigen.sh" \
  "$ROOT_DIR/preflight.sh" \
  "$ROOT_DIR/validate.sh" \
  "$ROOT_DIR/pi-gen-stage/01-tmba-files/00-run.sh" \
  "$ROOT_DIR/pi-gen-stage/02-tmba-install/00-run-chroot.sh" \
  "$ROOT_DIR/pi-gen-stage/03-tmba-hardware/00-run.sh" \
  "$ROOT_DIR/pi-gen-stage/04-tmba-services/00-run-chroot.sh" \
  "$ROOT_DIR/pi-gen-stage/05-tmba-finalize/00-run-chroot.sh"; do
  bash -n "$script"
done

grep -q '^dtoverlay=hifiberry-dacplus$' "$ROOT_DIR/pi-gen-stage/03-tmba-hardware/00-run.sh" || fail "HiFiBerry-Overlay fehlt"
grep -q "STAGE_LIST='stage0 stage1 stage2 stage-tmba'" "$ROOT_DIR/prepare-pigen.sh" || fail "pi-gen Stage-Liste fehlt"

echo "TMBA Image Builder-Konfiguration ist gültig."
