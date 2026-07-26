# TMBA Image Builder

Der Builder erzeugt das erste bootfähige TMBA-OS auf Basis von Raspberry Pi OS Lite Bookworm und dem festgelegten ARM64-Stand von `pi-gen`.

## Befehle

```bash
./image-builder/build.sh --preflight
./image-builder/build.sh --prepare
./image-builder/build.sh --dry-run
./image-builder/build.sh --build
./image-builder/build.sh --clean
```

## Ergebnis

Image, Buildprotokoll, Metadaten und `SHA256SUMS` liegen unter `image-builder/dist/`.

## Runtime im Image

- `/opt/tmba/backend`
- `/opt/tmba/backend/.venv`
- `/opt/tmba/config`
- `/etc/default/tmba-backend`
- `/etc/tmba-image-release`
- `/var/log/tmba/boot.log`
- `/var/log/tmba/healthcheck.log`

## Dienste

```text
tmba-boot-diagnostics.service -> tmba-backend.service -> tmba-healthcheck.service
```

Der Backend-Endpunkt ist nach dem Boot unter `http://tmba.local:8000/` erreichbar.
