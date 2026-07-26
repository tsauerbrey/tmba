# Installation TMBA v0.6.1-D

## Ziel

Dieser Teilmeilenstein verändert keine Produktionslogik. Er ergänzt
Vertragstests, API-Dokumentation, einen OpenAPI-Export und die abschließende
Release-Prüfung für TMBA v0.6.1.

## 1. Vorbedingungen

TMBA v0.6.1-C muss installiert und committed sein.

```bash
cd ~/Development/tmba
git status
git pull
```

## 2. Paket entpacken

```bash
cd ~/Downloads

unzip -o TMBA-0.6.1-D-Release-Hardening.zip \
  -d TMBA-0.6.1-D-Release-Hardening

cd ~/Downloads/TMBA-0.6.1-D-Release-Hardening

cp -R . ~/Development/tmba/
```

## 3. Skripte ausführbar machen

```bash
chmod +x \
  ~/Development/tmba/scripts/check-release-0.6.1.sh

chmod +x \
  ~/Development/tmba/scripts/export-openapi.py
```

## 4. Änderungen prüfen

```bash
cd ~/Development/tmba
git status
```

## 5. Release-Abschlussprüfung

```bash
./scripts/check-release-0.6.1.sh
```

Das Skript:

1. führt die neuen Vertragstests aus,
2. prüft alle AudioManager-, Pipeline- und API-Tests,
3. führt die vollständige Backend-Testsuite aus,
4. exportiert `docs/api/openapi.json`,
5. validiert das exportierte JSON,
6. prüft, ob `/audio/pipeline` dokumentiert ist.

## 6. Optional: Frontend-Build lokal prüfen

```bash
cd ~/Development/tmba/frontend
npm ci
npm run build
```

Falls dein Frontend-Verzeichnis anders heißt, verwende den bereits in deinem
GitHub-Workflow genutzten Pfad.

## 7. Commit und Push

```bash
cd ~/Development/tmba

git add .
git commit -m "Finalize AudioPipeline v0.6.1 release"
git push
```

Danach müssen die GitHub-Actions-Workflows wieder grün sein.
