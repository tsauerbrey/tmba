#!/bin/bash -e

install -d -o tmba -g tmba /opt/tmba /var/log/tmba

rm -rf \
  /opt/tmba/backend \
  /opt/tmba/ui \
  /opt/tmba/config \
  /opt/tmba/docs \
  /opt/tmba/assets \
  /opt/tmba/hardware

cp -a /opt/tmba/source/backend /opt/tmba/backend
cp -a /opt/tmba/source/ui /opt/tmba/ui
cp -a /opt/tmba/source/config /opt/tmba/config

for path in docs assets hardware; do
  if [ -e "/opt/tmba/source/${path}" ]; then
    cp -a "/opt/tmba/source/${path}" "/opt/tmba/${path}"
  fi
done

chown -R tmba:tmba /opt/tmba /var/log/tmba

chmod 0755 \
  /usr/local/lib/tmba/tmba-boot-diagnostics \
  /usr/local/lib/tmba/tmba-healthcheck \
  /opt/tmba/ui/start-tmba-ui.sh

sed -i \
  -e 's/__TMBA_RECEIVER_NAME__/TMBA/g' \
  -e 's/__TMBA_ALSA_DEVICE__/hw:0/g' \
  -e 's/__TMBA_MIXER_CONTROL__/Digital/g' \
  -e 's/__TMBA_MIXER_DEVICE__/hw:0/g' \
  /etc/shairport-sync.conf

# Backend-Python-Umgebung
python3 -m venv /opt/tmba/backend/.venv
/opt/tmba/backend/.venv/bin/python -m pip install --upgrade pip wheel setuptools
/opt/tmba/backend/.venv/bin/python \
  -m pip install --no-cache-dir \
  -r /opt/tmba/backend/requirements.txt

# Native Qt-Touchoberfläche
python3 -m venv /opt/tmba/ui/.venv
/opt/tmba/ui/.venv/bin/python -m pip install --upgrade pip wheel setuptools
/opt/tmba/ui/.venv/bin/python \
  -m pip install --no-cache-dir \
  -r /opt/tmba/ui/requirements.txt

# Konfiguration beim Build validieren
runuser -u tmba -- env PYTHONPATH=/opt/tmba/backend \
  /opt/tmba/backend/.venv/bin/python -c \
  'from tmba.core.config import get_settings; s=get_settings(); print(s.system.project.full_name, s.system.project.version)'

# Prüfen, ob PySide6 im ARM64-Image importiert werden kann
/opt/tmba/ui/.venv/bin/python -c \
  'import PySide6; print("PySide6", PySide6.__version__)'
