# Installation TMBA v0.6.1-A

Dieses Paket fügt die neue AudioPipeline parallel zum bestehenden AudioManager
hinzu. Bestehende Python-Quelldateien werden nicht ersetzt.

## 1. Projekt sichern und aktualisieren

```bash
cd ~/Development/tmba
git status
git pull
```

Der Arbeitsbaum sollte sauber sein.

## 2. Paket entpacken

```bash
cd ~/Downloads
unzip -o TMBA-0.6.1-A-AudioPipeline.zip \
  -d TMBA-0.6.1-A-AudioPipeline
```

## 3. Dateien kopieren

```bash
cd ~/Downloads/TMBA-0.6.1-A-AudioPipeline
cp -R . ~/Development/tmba/
```

## 4. Prüfskript ausführbar machen

```bash
chmod +x ~/Development/tmba/scripts/check-audio-pipeline.sh
```

## 5. Änderungen prüfen

```bash
cd ~/Development/tmba
git status
```

Erwartet werden neue Pipeline-, Test- und Dokumentationsdateien.

## 6. Tests ausführen

```bash
./scripts/check-audio-pipeline.sh
```

Erwartetes Gesamtergebnis:

```text
28 passed
```

Die genaue Zahl kann höher sein, falls zwischenzeitlich weitere Tests
hinzugefügt wurden.

## 7. Commit und Push

```bash
git add .
git commit -m "Add AudioPipeline architecture"
git push
```

Danach GitHub Actions kontrollieren. Beide Workflows müssen grün sein.

## 8. Optionaler Arbeitstag

Für Teilmeilensteine verwenden wir zunächst Commits und keinen offiziellen
SemVer-Tag. Ein offizieller Tag `v0.6.1` wird nach Abschluss von A bis D gesetzt.

Wer dennoch einen temporären Entwicklungs-Tag verwenden möchte:

```bash
git tag -a v0.6.1-a -m "TMBA v0.6.1-A AudioPipeline architecture"
git push origin v0.6.1-a
```
