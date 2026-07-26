#!/bin/bash -e
cat > /etc/tmba-image-release <<EOT
TMBA_IMAGE_VERSION=0.7.3-C
TMBA_IMAGE_VARIANT=developer
EOT
apt-get clean
rm -rf /var/lib/apt/lists/*
