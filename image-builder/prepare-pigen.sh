#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$ROOT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT_DIR/lib/common.sh"
# shellcheck disable=SC1091
source "$ROOT_DIR/config/image.env"

require_command git
require_command rsync
CACHE_DIR="$ROOT_DIR/cache"
PIGEN_DIR="$CACHE_DIR/pi-gen"
mkdir -p "$CACHE_DIR"

if [[ ! -d "$PIGEN_DIR/.git" ]]; then
  info "Klone pi-gen ($TMBA_PI_GEN_REF) …"
  git clone --branch "$TMBA_PI_GEN_REF" "$TMBA_PI_GEN_REPOSITORY" "$PIGEN_DIR"
else
  info "Aktualisiere vorhandenen pi-gen-Checkout …"
  git -C "$PIGEN_DIR" fetch --prune origin "$TMBA_PI_GEN_REF"
fi

git -C "$PIGEN_DIR" checkout --detach "$TMBA_PI_GEN_COMMIT"
actual_commit="$(git -C "$PIGEN_DIR" rev-parse HEAD)"
[[ "$actual_commit" == "$TMBA_PI_GEN_COMMIT" ]] || fail "pi-gen-Commit stimmt nicht überein."

rm -rf "$PIGEN_DIR/tmba-repo"
mkdir -p "$PIGEN_DIR/tmba-repo"
rsync -a --delete \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
  --exclude '.pytest_cache' --exclude 'node_modules' \
  --exclude 'image-builder/cache' --exclude 'image-builder/dist' \
  "$REPO_DIR/" "$PIGEN_DIR/tmba-repo/"

rm -rf "$PIGEN_DIR/stage-tmba"
cp -R "$ROOT_DIR/pi-gen-stage" "$PIGEN_DIR/stage-tmba"
rm -f "$PIGEN_DIR/stage2/EXPORT_IMAGE" "$PIGEN_DIR/stage2/EXPORT_NOOBS"

cat > "$PIGEN_DIR/config-tmba" <<EOT
IMG_NAME='$TMBA_IMAGE_NAME'
PI_GEN_RELEASE='TMBA Developer Image $TMBA_IMAGE_VERSION'
RELEASE='$TMBA_BASE_RELEASE'
ARCH='$TMBA_TARGET_ARCH'
DEPLOY_COMPRESSION='$TMBA_DEPLOY_COMPRESSION'
ENABLE_SSH='$TMBA_ENABLE_SSH'
FIRST_USER_NAME='$TMBA_DEFAULT_USER'
FIRST_USER_PASS='tmba'
DISABLE_FIRST_BOOT_USER_RENAME=1
TARGET_HOSTNAME='$TMBA_DEFAULT_HOSTNAME'
LOCALE_DEFAULT='$TMBA_LOCALE'
TIMEZONE_DEFAULT='$TMBA_TIMEZONE'
KEYBOARD_KEYMAP='de'
KEYBOARD_LAYOUT='German'
STAGE_LIST='stage0 stage1 stage2 stage-tmba'
EOT

printf '%s\n' "$actual_commit" > "$CACHE_DIR/pi-gen.commit"
info "pi-gen reproduzierbar vorbereitet: $actual_commit"
