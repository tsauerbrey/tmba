#!/bin/bash -e
systemctl enable ssh.service
systemctl enable avahi-daemon.service
systemctl enable shairport-sync.service
systemctl enable tmba-backend.service
