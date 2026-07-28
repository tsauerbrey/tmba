#!/bin/sh
set -eu

export HOME=/root
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/tmba-ui
export QT_QPA_PLATFORM=xcb
export QT_X11_NO_MITSHM=1

install -d -m 0700 "${XDG_RUNTIME_DIR}"

# Bildschirmabschaltung und Display-Standby deaktivieren.
xset s off
xset s noblank
xset -dpms

exec /opt/tmba/ui/.venv/bin/python /opt/tmba/ui/app.py
