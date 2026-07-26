#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$ROOT_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT_DIR/lib/common.sh"
# shellcheck disable=SC1091
source "$ROOT_DIR/config/image.env"

bytes_to_gib() { awk -v b="$1" 'BEGIN { printf "%.1f", b/1024/1024/1024 }'; }

info "Prüfe Host-Werkzeuge …"
for cmd in docker git rsync awk sed find tee shasum; do require_command "$cmd"; done

[[ "$REPO_DIR" != *" "* ]] || fail "Der Projektpfad darf keine Leerzeichen enthalten: $REPO_DIR"

info "Prüfe freien Speicher …"
free_kib="$(df -Pk "$ROOT_DIR" | awk 'NR==2 {print $4}')"
[[ "$free_kib" =~ ^[0-9]+$ ]] || fail "Freier Speicher konnte nicht ermittelt werden."
min_kib=$((TMBA_MIN_FREE_GIB * 1024 * 1024))
(( free_kib >= min_kib )) || fail "Zu wenig freier Speicher: mindestens ${TMBA_MIN_FREE_GIB} GiB erforderlich."
info "Freier Speicher: $((free_kib / 1024 / 1024)) GiB"

info "Prüfe Docker Engine …"
docker info >/dev/null 2>&1 || fail "Docker ist nicht gestartet oder nicht erreichbar."
server_arch="$(docker info --format '{{.Architecture}}')"
case "$server_arch" in arm64|aarch64) ;; *) fail "Docker-Serverarchitektur ist '$server_arch', erwartet wird ARM64." ;; esac

docker_cpus="$(docker info --format '{{.NCPU}}')"
docker_mem_bytes="$(docker info --format '{{.MemTotal}}')"
[[ "$docker_cpus" =~ ^[0-9]+$ ]] || fail "Docker-CPU-Anzahl konnte nicht ermittelt werden."
[[ "$docker_mem_bytes" =~ ^[0-9]+$ ]] || fail "Docker-Arbeitsspeicher konnte nicht ermittelt werden."
min_mem_bytes=$((TMBA_MIN_DOCKER_MEMORY_GIB * 1024 * 1024 * 1024))
(( docker_cpus >= TMBA_MIN_DOCKER_CPUS )) || fail "Docker benötigt mindestens ${TMBA_MIN_DOCKER_CPUS} CPUs; verfügbar: $docker_cpus."
(( docker_mem_bytes >= min_mem_bytes )) || fail "Docker benötigt mindestens ${TMBA_MIN_DOCKER_MEMORY_GIB} GiB RAM; verfügbar: $(bytes_to_gib "$docker_mem_bytes") GiB."
info "Docker: ${docker_cpus} CPUs, $(bytes_to_gib "$docker_mem_bytes") GiB RAM, Architektur ${server_arch}"

info "Prüfe ARM64-Container …"
docker run --rm --platform "$TMBA_DOCKER_PLATFORM" alpine:3.22 uname -m | grep -Eq '^(aarch64|arm64)$' \
  || fail "Ein ARM64-Testcontainer konnte nicht korrekt ausgeführt werden."

info "Build-Voraussetzungen sind erfüllt."
