#!/bin/bash -e
install -d -o tmba -g tmba /opt/tmba
rm -rf /opt/tmba/backend
cp -a /opt/tmba/source/backend /opt/tmba/backend
chown -R tmba:tmba /opt/tmba

python3 -m venv /opt/tmba/backend/.venv
/opt/tmba/backend/.venv/bin/python -m pip install --upgrade pip wheel
/opt/tmba/backend/.venv/bin/python -m pip install -r /opt/tmba/backend/requirements.txt
