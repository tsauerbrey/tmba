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
    plan = BUILDER / "dist/tmba-developer-0.7.3-C-build-plan.txt"
    text = plan.read_text()
    assert "version=0.7.3-C" in text
    assert "pi_gen_ref=arm64" in text
    assert "docker_platform=linux/arm64" in text
    assert "pi_gen_commit=ca8aeed0ae300c2a89f55ce9617d5f96a27e99e5" in text
    assert "minimum_free_gib=35" in text
    assert "shairport-sync.service" in text


def test_custom_pigen_stage_is_exportable() -> None:
    stage = BUILDER / "pi-gen-stage"
    assert (stage / "EXPORT_IMAGE").is_file()
    assert (stage / "00-tmba-packages/00-packages").is_file()
    assert (stage / "05-tmba-finalize/00-run-chroot.sh").is_file()


def test_hifiberry_amp4_pro_overlay_is_configured() -> None:
    script = (BUILDER / "pi-gen-stage/03-tmba-hardware/00-run.sh").read_text()
    assert "dtoverlay=hifiberry-dacplus" in script
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


def test_prepare_uses_pinned_pigen_commit() -> None:
    env = (BUILDER / "config/image.env").read_text()
    script = (BUILDER / "prepare-pigen.sh").read_text()
    assert "TMBA_PI_GEN_COMMIT=" in env
    assert 'checkout --detach "$TMBA_PI_GEN_COMMIT"' in script


def test_build_writes_metadata_and_checksums() -> None:
    script = (BUILDER / "build.sh").read_text()
    assert "build-metadata.txt" in script
    assert "SHA256SUMS" in script
    assert "PIPESTATUS[0]" in script
