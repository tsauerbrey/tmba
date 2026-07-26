#!/bin/bash -e
cat > /etc/tmba-image-release <<EOT
TMBA_IMAGE_VERSION=0.8.4
TMBA_IMAGE_VARIANT=developer
TMBA_IMAGE_BASE=Raspberry Pi OS Lite Bookworm
EOT

cat > /etc/motd <<'EOT'
TMBA-OS 0.8.4 Developer Image
Backend: http://tmba.local:8000/
Status:  systemctl status tmba-backend
Logs:    journalctl -u tmba-backend -b
Diag:    /var/log/tmba/boot.log
EOT

rm -rf /opt/tmba/source
apt-get clean
rm -rf /var/lib/apt/lists/*
