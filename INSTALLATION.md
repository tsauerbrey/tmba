# Installation TMBA v0.6.1-B

## 1. Aktuellen Stand prüfen

```bash
cd ~/Development/tmba
git status
git pull
```

Der Arbeitsbaum sollte sauber sein und v0.6.1-A enthalten.

## 2. Paket entpacken

```bash
cd ~/Downloads
unzip -o TMBA-0.6.1-B-AudioManager-Integration.zip \
  -d TMBA-0.6.1-B-AudioManager-Integration
```

## 3. Dateien kopieren

```bash
cd ~/Downloads/TMBA-0.6.1-B-AudioManager-Integration
cp -R . ~/Development/tmba/
```

Dabei wird diese bestehende Datei vollständig ersetzt:

```text
backend/tmba/audio/manager.py
```

Die übrigen Dateien werden neu hinzugefügt.

## 4. Prüfskript ausführbar machen

```bash
chmod +x \
  ~/Development/tmba/scripts/check-audio-manager-pipeline.sh
```

## 5. Änderungen prüfen

```bash
cd ~/Development/tmba
git diff -- backend/tmba/audio/manager.py
git status
```

## 6. Tests ausführen

```bash
./scripts/check-audio-manager-pipeline.sh
```

Die genaue Testzahl kann durch weitere Tests im Repository variieren.
Entscheidend ist, dass alle drei Prüfschritte erfolgreich beendet werden.

## 7. Commit und Push

```bash
git add .
git commit -m "Integrate AudioPipeline with AudioManager"
git push
```

Danach müssen Backend-Tests und Frontend-Build in GitHub Actions grün sein.
