# ADR-0014: Raspberry-Pi-Images mit pi-gen erzeugen

## Status

Angenommen für TMBA v0.7.3-B.

## Kontext

TMBA benötigt ein reproduzierbares, bootfähiges ARM64-Image für den Raspberry Pi 4. Die Anwendung allein reicht nicht aus; Pakete, Benutzer, Hardware-Overlay, Systemdienste und Backend-Umgebung müssen bereits beim Image-Bau zusammengeführt werden.

## Entscheidung

TMBA verwendet das offizielle Raspberry-Pi-Werkzeug `pi-gen` mit dessen ARM64-Zweig. Der TMBA-Builder erzeugt eine zusätzliche `stage-tmba`, kopiert einen bereinigten Repository-Snapshot in den Build-Kontext und exportiert erst nach der TMBA-Stufe das Image.

Die eigene Stufe übernimmt:

1. Installation der Laufzeitpakete,
2. Übernahme des Backend-Quellstands,
3. Aufbau der Python-virtuellen Umgebung,
4. Aktivierung des HiFiBerry-Amp4-Pro-Overlays,
5. Aktivierung der Systemdienste,
6. Schreiben der Image-Versionsinformation.

## Folgen

- Der Image-Build ist auf macOS über Docker möglich.
- Das Image enthält exakt den beim Start des Builds kopierten TMBA-Stand.
- `pi-gen` wird im Cache gehalten; der aufgelöste Commit wird protokolliert.
- Der vollständige Build braucht viel Speicher und Zeit.
- Das Developer-Passwort ist nur eine Übergangslösung und muss später durch sicheren First-Boot-Provisioning ersetzt werden.
