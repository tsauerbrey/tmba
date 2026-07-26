#!/usr/bin/env python3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANAGER_FILE = PROJECT_ROOT / "backend/tmba/audio/manager.py"
CALL = "\n\nregister_default_sources()\n"

def main() -> None:
    content = MANAGER_FILE.read_text(encoding="utf-8")
    if CALL not in content:
        print("Hinweis: Abschließender Aufruf nicht gefunden oder bereits entfernt.")
        return
    MANAGER_FILE.write_text(content.replace(CALL, "\n", 1), encoding="utf-8")
    print("Import-time-Aufruf register_default_sources() aus manager.py entfernt.")

if __name__ == "__main__":
    main()
