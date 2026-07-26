from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "image-builder"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "LC_ALL": "C"},
    )


def test_version_matches_image_configuration() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    config = (BUILDER / "config/image.env").read_text(encoding="utf-8")
    assert f"TMBA_IMAGE_VERSION={version}" in config


def test_required_stage_order_exists() -> None:
    stages = sorted(path.name for path in (BUILDER / "stages").iterdir() if path.is_dir())
    assert stages == ["00-base", "10-audio", "20-network", "30-tmba", "40-finalize"]


def test_validator_succeeds() -> None:
    result = run("bash", "image-builder/validate.sh")
    assert result.returncode == 0, result.stderr
    assert "ist gültig" in result.stdout


def test_dry_run_generates_build_plan() -> None:
    result = run("bash", "image-builder/build.sh", "--dry-run")
    assert result.returncode == 0, result.stderr
    plan = BUILDER / "dist/tmba-developer-0.7.3-A-build-plan.txt"
    assert plan.is_file()
    text = plan.read_text(encoding="utf-8")
    assert "board=raspberry-pi-4" in text
    assert "arch=arm64" in text
    assert "shairport-sync" in text


def test_real_build_is_explicitly_blocked() -> None:
    result = run("bash", "image-builder/build.sh")
    assert result.returncode == 2
    assert "noch nicht freigeschaltet" in result.stderr
