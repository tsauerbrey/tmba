# Changelog

Alle wichtigen Änderungen an TMBA-OS werden in dieser Datei dokumentiert.

Das Format orientiert sich an „Keep a Changelog“. Die Versionsnummern folgen
dem Schema der semantischen Versionierung.

## [Unreleased]

## [0.8.2] – 2026-07-26

### Behoben

- benutzerdefinierte `stage-tmba` übernimmt das Root-Dateisystem aus `stage2`
- Buildabbruch `Unable to chroot/chdir ... stage-tmba/rootfs` behoben

### Tests

- Builder-Test für `prerun.sh` und `copy_previous` ergänzt


### Geplant

- zentrale AudioPipeline
- CamillaDSP-Anbindung
- ALSA-Ausgabe
- HiFiBerry-Hardwareintegration

## [0.6.0] – 2026-07-25

### Hinzugefügt

- zentraler AudioManager
- exklusive Auswahl einer Audioquelle
- definierte Audiozustände:
  - `stopped`
  - `starting`
  - `playing`
  - `paused`
  - `error`
- REST-Endpunkte für den AudioManager
- zentrale Weiterleitung von Wiedergabebefehlen
- Lautstärkeverwaltung
- Vorbereitung für DSP und Hardwareausgabe
- NetworkService
- WLAN-Status
- WLAN-Scan
- gespeicherte WLAN-Verbindungen
- WLAN-Verbindung und Trennung
- WLAN-Oberfläche mit Bildschirmtastatur
- SystemService
- System- und Gesundheitsendpunkte
- AirPlay-Service
- Bluetooth-Service
- Artwork-Service
- Webradio-Verwaltung
- automatische Backend-Tests

### Verbessert

- EventBus-Integration
- SourceManager
- Quellenumschaltung
- Backend-Struktur
- macOS-sicheres Entwicklungsverhalten

### Tests

- 16 Backend-Tests erfolgreich
