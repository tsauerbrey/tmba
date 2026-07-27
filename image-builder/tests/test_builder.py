from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "image-builder"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def test_version_matches_image_configuration() -> None:
    version = (ROOT / "VERSION").read_text().strip()
    env = (BUILDER / "config/image.env").read_text()
    assert f"TMBA_IMAGE_VERSION={version}" in env


def test_builder_validation_succeeds() -> None:
    result = run(str(BUILDER / "validate.sh"))
    assert result.returncode == 0, result.stderr
    assert "Konfiguration ist gültig" in result.stdout


def test_dry_run_creates_complete_plan() -> None:
    result = run(str(BUILDER / "build.sh"), "--dry-run")
    assert result.returncode == 0, result.stderr
    plan = BUILDER / "dist/tmba-developer-0.9.0-build-plan.txt"
    text = plan.read_text()
    assert "version=0.9.0" in text
    assert "pi_gen_ref=2026-06-18-raspios-bookworm-arm64" in text
    assert "docker_platform=linux/arm64" in text
    assert "pi_gen_commit=" in text
    assert "minimum_free_gib=35" in text
    assert "shairport-sync.service" in text


def test_custom_pigen_stage_is_exportable() -> None:
    stage = BUILDER / "pi-gen-stage"
    assert (stage / "EXPORT_IMAGE").is_file()
    assert (stage / "00-tmba-packages/00-packages").is_file()
    assert (stage / "05-tmba-finalize/00-run-chroot.sh").is_file()


def test_hifiberry_amp4_pro_overlay_is_configured() -> None:
    script = (BUILDER / "pi-gen-stage/03-tmba-hardware/00-run.sh").read_text()
    assert "dtoverlay=hifiberry-amp4pro" in script
    assert "dtparam=audio=on" in script


def test_backend_service_uses_image_virtualenv() -> None:
    unit = (BUILDER / "overlays/rootfs/etc/systemd/system/tmba-backend.service").read_text()
    assert "User=tmba" in unit
    assert "/opt/tmba/backend/.venv/bin/python" in unit


def test_build_requires_known_mode() -> None:
    result = run(str(BUILDER / "build.sh"), "--unknown")
    assert result.returncode != 0
    assert "Unbekannter Modus" in result.stderr


def test_preflight_script_checks_resources() -> None:
    text = (BUILDER / "preflight.sh").read_text()
    assert "TMBA_MIN_FREE_GIB" in text
    assert "TMBA_MIN_DOCKER_MEMORY_GIB" in text
    assert "TMBA_MIN_DOCKER_CPUS" in text
    assert "alpine:3.22" in text


def test_clean_mode_removes_generated_directories() -> None:
    cache = BUILDER / "cache/test-marker"
    dist = BUILDER / "dist/test-marker"
    cache.parent.mkdir(parents=True, exist_ok=True)
    dist.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("x")
    dist.write_text("x")
    result = run(str(BUILDER / "build.sh"), "--clean")
    assert result.returncode == 0, result.stderr
    assert not cache.exists()
    assert not dist.exists()
    assert (BUILDER / "dist").is_dir()


def test_prepare_uses_bookworm_release_and_commit_lock() -> None:
    env = (BUILDER / "config/image.env").read_text()
    script = (BUILDER / "prepare-pigen.sh").read_text()
    assert "TMBA_PI_GEN_REF=2026-06-18-raspios-bookworm-arm64" in env
    assert 'rev-parse "${TMBA_PI_GEN_REF}^{commit}"' in script
    assert "COMMIT_LOCK" in script
    assert "actual_commit" in script
    assert 'docker image rm -f pi-gen:latest' in script


def test_build_writes_metadata_and_checksums() -> None:
    script = (BUILDER / "build.sh").read_text()
    assert "build-metadata.txt" in script
    assert "SHA256SUMS" in script
    assert "PIPESTATUS[0]" in script


def test_runtime_configuration_is_installed() -> None:
    install = (BUILDER / "pi-gen-stage/02-tmba-install/00-run-chroot.sh").read_text()
    assert "source/config" in install
    assert "/opt/tmba/config" in install
    assert "get_settings" in install


def test_boot_diagnostics_service_is_enabled() -> None:
    service = (BUILDER / "overlays/rootfs/etc/systemd/system/tmba-boot-diagnostics.service").read_text()
    script = BUILDER / "overlays/rootfs/usr/local/lib/tmba/tmba-boot-diagnostics"
    enable = (BUILDER / "pi-gen-stage/04-tmba-services/00-run-chroot.sh").read_text()
    assert "Before=tmba-backend.service" in service
    assert script.is_file()
    assert "tmba-boot-diagnostics.service" in enable


def test_backend_has_startup_healthcheck() -> None:
    service = (BUILDER / "overlays/rootfs/etc/systemd/system/tmba-healthcheck.service").read_text()
    script = (BUILDER / "overlays/rootfs/usr/local/lib/tmba/tmba-healthcheck").read_text()
    assert "After=tmba-backend.service" in service
    assert "/system/health" in script
    assert "seq 1 30" in script


def test_backend_listens_on_image_network() -> None:
    env = (BUILDER / "overlays/rootfs/etc/default/tmba-backend").read_text()
    unit = (BUILDER / "overlays/rootfs/etc/systemd/system/tmba-backend.service").read_text()
    assert "TMBA_BACKEND_HOST=0.0.0.0" in env
    assert "EnvironmentFile=-/etc/default/tmba-backend" in unit
    assert "ExecStartPre=" in unit



def test_custom_stage_copies_previous_rootfs() -> None:
    prerun = BUILDER / "pi-gen-stage/prerun.sh"
    text = prerun.read_text()
    assert prerun.is_file()
    assert "copy_previous" in text
    assert '${ROOTFS_DIR}' in text

def test_hardware_asset_uses_stage_dir() -> None:
    stage = BUILDER / "pi-gen-stage"
    script = (stage / "03-tmba-hardware/00-run.sh").read_text()
    assert (stage / "03-tmba-hardware/99-tmba-audio.conf").is_file()
    assert "${STAGE_DIR}/03-tmba-hardware/99-tmba-audio.conf" in script
    assert "files/99-tmba-audio.conf" not in script


def test_runtime_check_uses_runuser_without_sudo() -> None:
    install = (BUILDER / "pi-gen-stage/02-tmba-install/00-run-chroot.sh").read_text()
    assert "runuser -u tmba -- env" in install
    assert "sudo -u tmba" not in install


def test_all_release_versions_are_v090() -> None:
    version = (ROOT / "VERSION").read_text().strip()
    image_env = (BUILDER / "config/image.env").read_text()
    system = (ROOT / "config/system.yaml").read_text()
    finalize = (BUILDER / "pi-gen-stage/05-tmba-finalize/00-run-chroot.sh").read_text()
    assert version == "0.9.0"
    assert "TMBA_IMAGE_VERSION=0.9.0" in image_env
    assert "version: 0.9.0" in system
    assert "TMBA_IMAGE_VERSION=0.9.0" in finalize
    assert "TMBA-OS 0.9.0" in finalize


def test_pigen_loop_patch_replaces_stale_partition_nodes() -> None:
    patch = BUILDER / "patches/pi-gen/0001-refresh-stale-loop-partition-nodes.patch"
    text = patch.read_text()
    prepare = (BUILDER / "prepare-pigen.sh").read_text()
    assert patch.is_file()
    assert "Replacing stale /dev/$partition" in text
    assert "stat -c '%t'" in text
    assert "stat -c '%T'" in text
    assert 'rm -f "/dev/$partition"' in text
    assert 'git -C "$PIGEN_DIR" apply' in prepare


def test_check_script_reads_version_dynamically() -> None:
    script = (ROOT / "scripts/check-image-builder.sh").read_text()
    assert 'VERSION="$(cat "$ROOT_DIR/VERSION")"' in script
    assert "v0.8.2" not in script
