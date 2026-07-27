#!/bin/bash -e
CONFIG_TXT="${ROOTFS_DIR}/boot/firmware/config.txt"
if [ ! -f "$CONFIG_TXT" ]; then
  CONFIG_TXT="${ROOTFS_DIR}/boot/config.txt"
fi

sed -i '/^[[:space:]]*dtparam=audio=on[[:space:]]*$/d' "$CONFIG_TXT"
grep -q '^dtoverlay=hifiberry-amp4pro$' "$CONFIG_TXT" || cat >> "$CONFIG_TXT" <<'EOT'

# TMBA: HiFiBerry Amp4 Pro
dtoverlay=hifiberry-amp4pro
EOT

install -Dm644 \
  "${STAGE_DIR}/03-tmba-hardware/99-tmba-audio.conf" \
  "${ROOTFS_DIR}/etc/modprobe.d/99-tmba-audio.conf"
