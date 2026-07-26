#!/usr/bin/env bash
set -Eeuo pipefail

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
info() { printf '[%s] [TMBA] %s\n' "$(timestamp)" "$*"; }
warn() { printf '[%s] [TMBA] Warnung: %s\n' "$(timestamp)" "$*" >&2; }
fail() { printf '[%s] [TMBA] Fehler: %s\n' "$(timestamp)" "$*" >&2; exit 1; }
require_command() { command -v "$1" >/dev/null 2>&1 || fail "Programm fehlt: $1"; }
repo_version() { tr -d '[:space:]' < "$1/VERSION"; }
