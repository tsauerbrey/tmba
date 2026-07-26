#!/usr/bin/env python3
"""Export the current TMBA FastAPI OpenAPI document."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
OUTPUT_FILE = PROJECT_ROOT / "docs/api/openapi.json"

sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from tmba.main import app  # noqa: E402


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(
            app.openapi(),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"OpenAPI-Dokument exportiert: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
