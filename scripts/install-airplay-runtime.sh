#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Fehler: Dieses Skript muss mit sudo ausgeführt werden." >&2
  exit 1
fi

RECEIVER_NAME="${1:-TMBA}"
ALSA_DEVICE="${2:-hw:sndrpihifiberry}"
MIXER_CONTROL="${3:-Digital}"
MIXER_DEVICE="${4:-$ALSA_DEVICE}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT_DIR/config/shairport-sync/tmba.conf.template"
OVERRIDE="$ROOT_DIR/config/shairport-sync/tmba-override.conf"
TARGET_CONFIG="/etc/shairport-sync.conf"
OVERRIDE_DIR="/etc/systemd/system/shairport-sync.service.d"

command -v apt-get >/dev/null || {
  echo "Fehler: Dieses Installationsskript unterstützt Debian/Raspberry Pi OS mit apt." >&2
  exit 1
}

[[ -f "$TEMPLATE" ]] || { echo "Fehler: Vorlage fehlt: $TEMPLATE" >&2; exit 1; }
[[ -f "$OVERRIDE" ]] || { echo "Fehler: systemd-Override fehlt: $OVERRIDE" >&2; exit 1; }

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y shairport-sync avahi-daemon alsa-utils

if [[ -f "$TARGET_CONFIG" ]]; then
  cp -a "$TARGET_CONFIG" "${TARGET_CONFIG}.tmba-backup-$(date +%Y%m%d-%H%M%S)"
fi

escape_sed() { printf '%s' "$1" | sed 's/[&|]/\\&/g'; }
receiver="$(escape_sed "$RECEIVER_NAME")"
device="$(escape_sed "$ALSA_DEVICE")"
control="$(escape_sed "$MIXER_CONTROL")"
mixer="$(escape_sed "$MIXER_DEVICE")"

sed \
  -e "s|__TMBA_RECEIVER_NAME__|$receiver|g" \
  -e "s|__TMBA_ALSA_DEVICE__|$device|g" \
  -e "s|__TMBA_MIXER_CONTROL__|$control|g" \
  -e "s|__TMBA_MIXER_DEVICE__|$mixer|g" \
  "$TEMPLATE" > "$TARGET_CONFIG"
chmod 0644 "$TARGET_CONFIG"

install -d -m 0755 "$OVERRIDE_DIR"
install -m 0644 "$OVERRIDE" "$OVERRIDE_DIR/tmba.conf"

systemctl daemon-reload
systemctl enable --now avahi-daemon.service
systemctl enable shairport-sync.service
systemctl restart shairport-sync.service

printf '\nTMBA AirPlay-Laufzeit wurde installiert.\n'
printf 'Empfängername: %s\n' "$RECEIVER_NAME"
printf 'ALSA-Gerät:    %s\n\n' "$ALSA_DEVICE"
systemctl --no-pager --full status shairport-sync.service || true
