# TMBA-OS Roadmap

Diese Roadmap beschreibt die geplanten Entwicklungsschritte. Einzelne
Versionen können bei Bedarf aufgeteilt werden.

## v0.6.1 – AudioPipeline-Architektur

Ziel: Eine stabile und erweiterbare Pipeline zwischen AudioManager und
Hardwareausgabe.

Geplant:

- `AudioPipeline`
- definierte Pipeline-Zustände
- Pipeline-Konfiguration
- Source Gain
- zentrale Lautstärke
- Output Gain
- Limiter-Vorbereitung
- DSP-Schnittstelle
- Output-Schnittstelle
- Simulationsmodus für macOS
- Tests
- technische Architekturdokumentation

## v0.6.2 – CamillaDSP

Ziel: Alle Audioquellen über denselben DSP-Prozess führen.

Geplant:

- CamillaDSP-Prozessverwaltung
- Konfigurationsgenerierung
- DSP-Status
- Start, Stop und Neustart
- Presets
- Fehlerbehandlung
- sichere Simulation auf macOS

## v0.6.3 – ALSA-Ausgabe

Ziel: Einheitliche Hardwareausgabe auf dem Raspberry Pi.

Geplant:

- ALSA-Geräteerkennung
- Auswahl des Ausgabegeräts
- Sample-Rate-Konfiguration
- Format-Konfiguration
- Puffer und Latenz
- XRUN-Erkennung
- Fallback-Verhalten

## v0.7.0 – HiFiBerry-Integration

Ziel: Reale Ausgabe über HiFiBerry Amp4 Pro und DSP Add-on.

Geplant:

- Geräteerkennung
- Boot-Konfiguration
- Mixer-Steuerung
- Verstärker-Lautstärke
- DSP Add-on
- sichere Start- und Abschaltsequenz
- Hardwaretests

## v0.8.0 – Touch-Oberfläche

Ziel: Vollständig bedienbare Oberfläche auf dem 7-Zoll-Display.

Geplant:

- Hauptansicht
- Quellenwahl
- Now Playing
- Lautstärke
- Webradio
- Bluetooth
- AirPlay
- DSP
- WLAN
- Systeminformationen
- 800 × 480 Optimierung
- Kiosk-Modus

## v0.9.0 – Hardwarebedienung

Ziel: Bedienung ohne Touchscreen ermöglichen.

Geplant:

- Drehencoder
- Drucktaster
- Langdruck
- IR-Empfänger
- Fernbedienungszuordnung
- Lautstärke
- Quellenwahl
- Wiedergabesteuerung
- Herunterfahren

## v1.0.0 – Erstes bootfähiges Image

Ziel: Installierbares und reproduzierbares TMBA-OS-Image.

Geplant:

- Image Builder
- automatisierte Installation
- Splashscreen
- versteckter Boottext
- Kiosk-Autostart
- Dienste und Abhängigkeiten
- Wiederherstellung der letzten Quelle
- WLAN-Ersteinrichtung
- Update-Konzept
- vollständige Installationsdokumentation
