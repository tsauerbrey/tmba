#!/bin/bash -e

# A custom pi-gen stage needs its own root filesystem. Reuse the complete
# rootfs produced by the preceding stage (stage2) before running TMBA steps.
if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi
