# Installation TMBA v0.7.1-A

## 1. Paket entpacken

```bash
cd ~/Downloads

unzip -o TMBA-0.7.1-A-AudioSource-API.zip \
  -d TMBA-0.7.1-A-AudioSource-API
```

Das ZIP enthält direkt `backend/`, `.github/`, `docs/`, `scripts/` und
`INSTALLATION.md`. Es gibt keine zusätzliche innere Paketebene.

## 2. Dateien in das Repository kopieren

```bash
cd ~/Downloads/TMBA-0.7.1-A-AudioSource-API
cp -R . ~/Development/tmba/
```

## 3. Prüfskript ausführen

```bash
chmod +x ~/Development/tmba/scripts/check-audio-source-api.sh
cd ~/Development/tmba
./scripts/check-audio-source-api.sh
```

Erwartete Abschlussmeldung:

```text
TMBA v0.7.1-A erfolgreich geprüft.
```

## 4. GitHub aktualisieren

```bash
git status
git add .
git commit -m "Release v0.7.1-A: AudioSource API and backend CI"
git push
git status
```

Nach dem Push startet GitHub Actions automatisch die Backend-Tests. Nach
erfolgreichem Abschluss wird zusätzlich ein ZIP-Artefakt des Repository-Stands
erzeugt.
