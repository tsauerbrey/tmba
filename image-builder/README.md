# TMBA Developer Image Builder

Der Image Builder beschreibt reproduzierbar die Grundlage des späteren TMBA-OS-Images.
In v0.7.3-A wird bewusst noch kein vollständiges Raspberry-Pi-Image gebaut. Stattdessen werden Zielplattform, Paketlisten, Stufen, Overlays und Validierungen festgelegt.

## Zielplattform

- Raspberry Pi 4 Model B
- ARM64 / aarch64
- Raspberry Pi OS Lite 64 Bit
- Debian Bookworm-kompatible Basis
- Headless-Entwicklersystem mit SSH

## Befehle

```bash
./image-builder/validate.sh
./image-builder/build.sh --dry-run
```

Ein echter Build ist in v0.7.3-A noch gesperrt. `--dry-run` erzeugt einen Buildplan unter `image-builder/dist/`.

## Struktur

- `config/`: deklarative Ziel- und Imagekonfiguration
- `packages/`: Paketlisten
- `stages/`: geordnete Buildstufen
- `overlays/`: spätere Dateisystem-Overlays
- `tests/`: Builder-Tests
- `dist/`: lokal erzeugte, nicht versionierte Buildpläne
