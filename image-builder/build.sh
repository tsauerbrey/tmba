#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$ROOT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT_DIR/lib/common.sh"
# shellcheck disable=SC1091
source "$ROOT_DIR/config/image.env"
MODE="${1:---build}"
DIST_DIR="$ROOT_DIR/dist"
CACHE_DIR="$ROOT_DIR/cache"
mkdir -p "$DIST_DIR"

write_plan() {
  local plan="$DIST_DIR/${TMBA_IMAGE_NAME}-${TMBA_IMAGE_VERSION}-build-plan.txt"
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
    echo "pi_gen_ref=$TMBA_PI_GEN_REF"
    if [[ -s "$CACHE_DIR/pi-gen.commit" ]]; then
      echo "pi_gen_commit=$(cat "$CACHE_DIR/pi-gen.commit")"
    elif [[ -n "${TMBA_PI_GEN_COMMIT:-}" ]]; then
      echo "pi_gen_commit=$TMBA_PI_GEN_COMMIT"
    else
      echo "pi_gen_commit=pending-prepare"
    fi
    echo "docker_platform=$TMBA_DOCKER_PLATFORM"
    echo "minimum_free_gib=$TMBA_MIN_FREE_GIB"
    echo
    echo "packages:"
    cat "$ROOT_DIR"/packages/*.txt "$ROOT_DIR"/pi-gen-stage/00-tmba-packages/00-packages | awk 'NF && $1 !~ /^#/ {print $1}' | sort -u | sed 's/^/- /'
    echo
    echo "services:"
    awk 'NF && $1 !~ /^#/ {print "- "$1}' "$ROOT_DIR/config/services.txt"
  } > "$plan"
  info "Buildplan erzeugt: ${plan#$REPO_DIR/}"
}

clean_builder() {
  info "Entferne Builder-Cache und erzeugte Artefakte …"
  rm -rf "$CACHE_DIR" "$DIST_DIR"
  mkdir -p "$DIST_DIR"
  info "Builder ist bereinigt."
}

run_build() {
  "$ROOT_DIR/preflight.sh"
  "$ROOT_DIR/prepare-pigen.sh"
  write_plan
  local pigen_dir="$CACHE_DIR/pi-gen"
  local log_file="$DIST_DIR/${TMBA_IMAGE_NAME}-${TMBA_IMAGE_VERSION}-build.log"
  local meta_file="$DIST_DIR/${TMBA_IMAGE_NAME}-${TMBA_IMAGE_VERSION}-build-metadata.txt"
  local started finished status=0
  started="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  info "Starte pi-gen-Docker-Build. Das kann deutlich länger dauern."
  set +e
  (
    cd "$pigen_dir"
    export PRESERVE_CONTAINER=0
    ./build-docker.sh -c config-tmba
  ) 2>&1 | tee "$log_file"
  status=${PIPESTATUS[0]}
  set -e
  finished="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  {
    echo "version=$TMBA_IMAGE_VERSION"
    echo "started_utc=$started"
    echo "finished_utc=$finished"
    echo "exit_status=$status"
    if [[ -s "$CACHE_DIR/pi-gen.commit" ]]; then
      echo "pi_gen_commit=$(cat "$CACHE_DIR/pi-gen.commit")"
    elif [[ -n "${TMBA_PI_GEN_COMMIT:-}" ]]; then
      echo "pi_gen_commit=$TMBA_PI_GEN_COMMIT"
    else
      echo "pi_gen_commit=pending-prepare"
    fi
    echo "host_arch=$(uname -m)"
    echo "docker_server_arch=$(docker info --format '{{.Architecture}}')"
  } > "$meta_file"
  (( status == 0 )) || fail "pi-gen-Build fehlgeschlagen (Status $status). Protokoll: ${log_file#$REPO_DIR/}"

  find "$pigen_dir/deploy" -maxdepth 1 -type f \( -name '*.img.xz' -o -name '*.img' -o -name '*.zip' \) -exec cp -f {} "$DIST_DIR/" \;
  rm -f "$DIST_DIR/SHA256SUMS"
  (cd "$DIST_DIR" && find . -maxdepth 1 -type f \( -name '*.img.xz' -o -name '*.img' -o -name '*.zip' \) -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS)
  [[ -s "$DIST_DIR/SHA256SUMS" ]] || fail "Kein Image-Artefakt im pi-gen-Deploy-Verzeichnis gefunden."
  info "Build abgeschlossen. Artefakte liegen in image-builder/dist/."
}

"$ROOT_DIR/validate.sh"
case "$MODE" in
  --dry-run) write_plan ;;
  --preflight) "$ROOT_DIR/preflight.sh" ;;
  --prepare) "$ROOT_DIR/prepare-pigen.sh"; write_plan ;;
  --clean) clean_builder ;;
  --build) run_build ;;
  *) fail "Unbekannter Modus: $MODE (erlaubt: --dry-run, --preflight, --prepare, --clean, --build)" ;;
esac
