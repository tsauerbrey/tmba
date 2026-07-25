# TMBA-OS

**TMBA** steht für **Thoralfs Mobile Beschallungs-Anlage**.

TMBA-OS ist eine speziell entwickelte Audio-Plattform für den Raspberry Pi.  
Das System verbindet Webradio, AirPlay und Bluetooth mit einer gemeinsamen
Audio-Pipeline, DSP-Verarbeitung und einer für Touch-Bedienung optimierten
Benutzeroberfläche.

## Projektziel

TMBA-OS soll als stabile, mobile und vollständig kontrollierbare
Beschallungsanlage eingesetzt werden. Alle Audioquellen sollen über denselben
Signalweg laufen:

```text
Webradio ─┐
Bluetooth ├──> AudioManager ──> AudioPipeline ──> CamillaDSP ──> ALSA
AirPlay ──┘                                                │
                                                           └──> HiFiBerry Amp4 Pro
```

## Geplante Hauptfunktionen

- Webradio mit Favoriten und Sendersuche
- AirPlay-Empfang
- Bluetooth-Audio
- zentrale Quellenumschaltung
- gemeinsame DSP-Pipeline für alle Quellen
- CamillaDSP
- Equalizer, Loudness und Lautsprecherprofile
- HiFiBerry Amp4 Pro
- HiFiBerry DSP Add-on
- Touch-Oberfläche für 800 × 480 Pixel
- WLAN-Verwaltung mit Bildschirmtastatur
- Drehencoder
- IR-Fernbedienung
- Kiosk-Modus
- automatischer Start
- Wiederherstellung der zuletzt verwendeten Quelle
- bootfähiges Raspberry-Pi-Image

## Zielhardware

- Raspberry Pi 4B
- Raspberry Pi 7-Zoll-DSI-Touchdisplay, 800 × 480 Pixel
- HiFiBerry Amp4 Pro
- HiFiBerry DSP Add-on
- Bourns PEC11R Drehencoder
- KY-022 IR-Empfänger

## Softwarearchitektur

### Backend

- Python
- FastAPI
- EventBus
- SourceManager
- AudioManager
- Dienste für Webradio, Bluetooth, AirPlay, Netzwerk und Systemstatus
- MPD für Webradio
- später CamillaDSP, PipeWire beziehungsweise ALSA

### Frontend

- Vue 3
- Pinia
- Vite
- responsive Touch-Oberfläche

## Aktueller Entwicklungsstand

**Version: v0.6.0**

Bereits vorhanden:

- FastAPI-Backend
- Vue-Frontend
- EventBus
- SourceManager
- zentraler AudioManager
- Webradio-Backend
- AirPlay-Service
- Bluetooth-Service
- Artwork-Service
- SystemService
- NetworkService
- WLAN-Oberfläche
- automatische Tests

Aktueller Teststand:

```text
16 Tests erfolgreich
```

## Repository-Struktur

```text
tmba/
├── backend/
├── frontend/
├── config/
├── docs/
├── hardware/
├── images/
├── scripts/
├── assets/
├── CHANGELOG.md
├── ROADMAP.md
├── CONTRIBUTING.md
└── README.md
```

## Lokale Entwicklung

### Backend starten

```bash
cd backend
source .venv/bin/activate
uvicorn tmba.main:app --reload
```

Backend-Dokumentation:

```text
http://127.0.0.1:8000/docs
```

### Backend testen

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python -m pytest -q
```

### Frontend starten

```bash
cd frontend
npm install
npm run dev
```

## Entwicklungsprinzipien

- kleine, testbare Meilensteine
- eine zentrale Audio-Pipeline
- keine parallelen oder doppelten Audiowege
- sichere Simulation auf macOS
- reale Hardware-Anbindung erst nach stabiler Architektur
- vollständige Tests vor jedem Release
- Git-Tag für jeden stabilen Meilenstein

## Roadmap

Die geplanten Versionen stehen in [ROADMAP.md](ROADMAP.md).

## Änderungen

Alle Änderungen stehen in [CHANGELOG.md](CHANGELOG.md).

## Lizenz

Die endgültige Lizenz wird vor der ersten öffentlichen Veröffentlichung
festgelegt. Bis dahin gilt: Alle Rechte vorbehalten.
