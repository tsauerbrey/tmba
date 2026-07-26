#!/bin/bash -e
install -d -m 0755 "${ROOTFS_DIR}/opt/tmba"
rsync -a --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude 'node_modules' \
  --exclude 'image-builder/cache' \
  --exclude 'image-builder/dist' \
  "${BASE_DIR}/tmba-repo/" "${ROOTFS_DIR}/opt/tmba/source/"

install -Dm644 "${BASE_DIR}/tmba-repo/image-builder/overlays/rootfs/etc/systemd/system/tmba-backend.service" \
  "${ROOTFS_DIR}/etc/systemd/system/tmba-backend.service"
install -Dm644 "${BASE_DIR}/tmba-repo/config/shairport-sync/tmba.conf.template" \
  "${ROOTFS_DIR}/etc/shairport-sync.conf"
install -Dm644 "${BASE_DIR}/tmba-repo/config/shairport-sync/tmba-override.conf" \
  "${ROOTFS_DIR}/etc/systemd/system/shairport-sync.service.d/tmba.conf"
