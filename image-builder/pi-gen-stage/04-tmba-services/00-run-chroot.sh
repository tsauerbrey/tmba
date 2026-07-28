#!/bin/bash -e

echo "[TMBA] Installiere systemd-Dienste..."

install -m 0644 \
    /opt/tmba/config/systemd/tmba-backend.service \
    /etc/systemd/system/tmba-backend.service

install -m 0644 \
    /opt/tmba/config/systemd/tmba-healthcheck.service \
    /etc/systemd/system/tmba-healthcheck.service

install -m 0644 \
    /opt/tmba/config/systemd/tmba-boot-diagnostics.service \
    /etc/systemd/system/tmba-boot-diagnostics.service

install -m 0644 \
    /opt/tmba/config/systemd/tmba-ui.service \
    /etc/systemd/system/tmba-ui.service

systemctl enable ssh.service
systemctl enable avahi-daemon.service
systemctl enable shairport-sync.service

systemctl enable tmba-boot-diagnostics.service
systemctl enable tmba-backend.service
systemctl enable tmba-healthcheck.service
systemctl enable tmba-ui.service

systemctl disable getty@tty1.service || true
systemctl mask getty@tty1.service || true

echo "[TMBA] Dienste eingerichtet."