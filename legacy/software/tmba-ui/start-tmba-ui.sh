#!/bin/sh
set -eu
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export QT_QPA_PLATFORM=xcb
export QT_X11_NO_MITSHM=1
exec /opt/tmba/ui/.venv/bin/python /opt/tmba/ui/app.py
