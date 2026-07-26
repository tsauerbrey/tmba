# TMBA Developer Image Builder

Der Builder erzeugt ein Raspberry-Pi-OS-Lite-Image für den Raspberry Pi 4 (ARM64). Das offizielle `pi-gen` wird als externe, auf einen exakten Commit festgelegte Build-Abhängigkeit im lokalen Cache verwendet. Die TMBA-Anpassungen bleiben vollständig in `pi-gen-stage/` und im Repository versioniert.

## Befehle

```bash
./image-builder/build.sh --dry-run
./image-builder/build.sh --preflight
./image-builder/build.sh --prepare
./image-builder/build.sh --clean
./image-builder/build.sh --build
```

- `--dry-run`: validiert und erzeugt den Buildplan.
- `--preflight`: prüft Docker, ARM64, CPU, RAM, Werkzeuge und freien Speicher.
- `--prepare`: lädt `pi-gen` und checkt den festgelegten Commit aus.
- `--clean`: entfernt nur Builder-Cache und Buildartefakte.
- `--build`: führt Preflight, Vorbereitung und vollständigen Docker-Build aus.

## Mindestanforderungen

- Docker Engine oder OrbStack
- ARM64-Docker-Server
- mindestens 4 Docker-CPUs
- mindestens 8 GiB Docker-RAM
- mindestens 35 GiB freier Speicher
- Git, rsync und Standard-Unix-Werkzeuge
- Projektpfad ohne Leerzeichen

## Reproduzierbarkeit

`config/image.env` enthält sowohl den Branch als auch den exakten `pi-gen`-Commit. `prepare-pigen.sh` checkt diesen Commit im Detached-HEAD-Modus aus. Ein späterer Stand des Remote-Branches verändert dadurch keinen bereits definierten TMBA-Build.

## Ausgaben

```text
image-builder/dist/
├── tmba-developer-0.7.3-C-build-plan.txt
├── tmba-developer-0.7.3-C-build.log
├── tmba-developer-0.7.3-C-build-metadata.txt
├── *.img.xz
└── SHA256SUMS
```

Das Developer Image verwendet vorläufig den Benutzer `tmba` mit dem Passwort `tmba`. Dieses Passwort ist nur für lokale Entwicklungstests vorgesehen.
