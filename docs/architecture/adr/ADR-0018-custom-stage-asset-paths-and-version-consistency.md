# ADR-0018: Robuste Asset-Pfade und konsistente Image-Version

## Status

Akzeptiert – 2026-07-26

## Kontext

Der erste Build mit funktionierendem Stage-Chaining erreichte den Hardware-Schritt,
brach dort jedoch beim Installieren von `99-tmba-audio.conf` ab. Das Skript verwendete
den relativen Pfad `files/99-tmba-audio.conf`, obwohl die Datei direkt im
Hardware-Schritt liegt. Außerdem meldete die Runtime-Konfiguration noch Version
`0.8.1`, während der Image-Builder bereits `0.8.2` erzeugte.

## Entscheidung

- Stage-Assets werden über `${STAGE_DIR}` adressiert.
- `99-tmba-audio.conf` wird explizit als erforderliche Builder-Datei validiert.
- `VERSION`, `TMBA_IMAGE_VERSION`, `config/system.yaml` und die Release-Datei im
  Image müssen dieselbe Versionsnummer enthalten.
- Benutzerkommandos im Chroot werden mit `runuser` statt `sudo` ausgeführt.

## Konsequenzen

Stage-Skripte sind unabhängig vom aktuellen Arbeitsverzeichnis. Fehlende Assets
und auseinanderlaufende Versionsnummern werden bereits vor dem mehrstündigen
Image-Build erkannt.
