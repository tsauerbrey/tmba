# ADR-0016: Bookworm-spezifische pi-gen-Release-Basis

- Status: Akzeptiert
- Datum: 2026-07-26

## Kontext

TMBA-OS 0.8.0 sollte Raspberry Pi OS Lite Bookworm erzeugen, verwendete jedoch einen `pi-gen`-Commit aus dem Trixie-orientierten ARM64-Zweig. Der Bootstrap war erfolgreich, der anschließende APT-Lauf scheiterte aber wegen eines nicht passenden Debian-Archivschlüsselbunds.

## Entscheidung

TMBA-OS Bookworm verwendet den offiziellen ARM64-Bookworm-Release-Tag `2026-06-18-raspios-bookworm-arm64`. Der Tag wird beim Vorbereiten in einen unveränderlichen Commit aufgelöst und lokal protokolliert.

## Folgen

- Basisbetriebssystem und Buildskripte gehören zur gleichen Raspberry-Pi-OS-Veröffentlichung.
- Die APT-Signaturprüfung bleibt unverändert aktiv.
- Ein Wechsel der Basis löscht inkompatible Build-Caches automatisch.
- Ein späterer Wechsel auf Trixie erfolgt als bewusster eigener Architekturentscheid.
