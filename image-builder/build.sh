#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$ROOT_DIR/.." && pwd)"
MODE="${1:-}"

if [[ "$MODE" != "--dry-run" ]]; then
  echo "Ein echter Image-Build ist in TMBA v0.7.3-A noch nicht freigeschaltet." >&2
  echo "Verwende: ./image-builder/build.sh --dry-run" >&2
  exit 2
fi

"$ROOT_DIR/validate.sh"
# shellcheck disable=SC1090
source "$ROOT_DIR/config/image.env"

DIST_DIR="$ROOT_DIR/dist"
PLAN_FILE="$DIST_DIR/${TMBA_IMAGE_NAME}-${TMBA_IMAGE_VERSION}-build-plan.txt"
mkdir -p "$DIST_DIR"

{
  echo "TMBA Developer Image Build Plan"
  echo "version=$TMBA_IMAGE_VERSION"
  echo "board=$TMBA_TARGET_BOARD"
  echo "arch=$TMBA_TARGET_ARCH"
  echo "base_os=$TMBA_BASE_OS"
  echo "base_release=$TMBA_BASE_RELEASE"
  echo "hostname=$TMBA_DEFAULT_HOSTNAME"
  echo "user=$TMBA_DEFAULT_USER"
  echo "ssh=$TMBA_ENABLE_SSH"
  echo
  echo "stages:"
  find "$ROOT_DIR/stages" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort | sed 's/^/- /'
  echo
  echo "packages:"
  cat "$ROOT_DIR"/packages/*.txt | awk 'NF && $1 !~ /^#/ {print $1}' | sort -u | sed 's/^/- /'
  echo
  echo "services:"
  awk 'NF && $1 !~ /^#/ {print "- "$1}' "$ROOT_DIR/config/services.txt"
} > "$PLAN_FILE"

echo "Dry-Run abgeschlossen: ${PLAN_FILE#$REPO_DIR/}"
