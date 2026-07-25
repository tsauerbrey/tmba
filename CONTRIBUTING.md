# Mitarbeit an TMBA-OS

## Grundprinzip

Jeder Entwicklungsschritt soll klein, nachvollziehbar und testbar bleiben.

## Empfohlener Ablauf

1. Aktuellen Stand von GitHub laden.
2. Neue Funktion in einem eigenen Branch entwickeln.
3. Tests ausführen.
4. Dokumentation aktualisieren.
5. Änderungen committen.
6. Branch nach Prüfung zusammenführen.
7. Stabilen Meilenstein mit einem Git-Tag kennzeichnen.

## Branch-Namen

Beispiele:

```text
feature/audio-pipeline
feature/camilladsp
feature/hifiberry
fix/webradio-stop
docs/architecture
```

## Commit-Nachrichten

Commit-Nachrichten sollen kurz und eindeutig sein.

Beispiele:

```text
Add central AudioManager
Add WiFi settings interface
Fix Webradio source synchronization
Document audio pipeline architecture
```

## Backend-Tests

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python -m pytest -q
```

## Frontend-Prüfung

```bash
cd frontend
npm install
npm run build
```

## Anforderungen vor einem Release

- Backend-Tests erfolgreich
- Frontend-Build erfolgreich
- Changelog aktualisiert
- Roadmap geprüft
- Versionsnummer geprüft
- Commit erstellt
- Git-Tag erstellt
- Änderungen zu GitHub übertragen
