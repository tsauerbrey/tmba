# TMBA Developer Guide

## Schichten

1. **API/UI** – externe Bedienung
2. **AudioEngine** – Anwendungslebenszyklus und koordinierter Status
3. **AudioManager** – Quellensteuerung und Transport
4. **AudioPipeline** – Verarbeitungsstufen und OutputDriver
5. **Systemdienste** – AirPlay, Bluetooth, Webradio, ALSA und später DSP

## Entwicklungsregeln

- Neue Hardware- oder Dienstlogik gehört nicht in REST-Routen.
- Die AudioEngine delegiert; sie implementiert keine Quellendetails.
- Öffentliche Statusdaten müssen stabil und serialisierbar sein.
- Fehler werden als strukturierte Ergebnisse und über den EventBus sichtbar.
- Jede neue Zustandsänderung benötigt Unit-Tests.
- Neue REST-Funktionen benötigen API-Tests.

## Testreihenfolge

1. betroffene Unit-Tests
2. betroffene API- oder Integrationstests
3. vollständige Backend-Tests

## Release-Ablauf

1. Paket installieren
2. Prüfskript ausführen
3. `git status` prüfen
4. Commit mit Versions- und Funktionsbezug
5. Push
6. sauberen Arbeitsbaum kontrollieren
