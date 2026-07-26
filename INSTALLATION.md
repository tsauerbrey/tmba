# Installation – TMBA v0.7.1-B

## 1. Entpacken

```bash
cd ~/Downloads

unzip -o TMBA-0.7.1-B-DummySource-PCM.zip \
  -d TMBA-0.7.1-B-DummySource-PCM
```

Das ZIP enthält direkt `backend/`, `docs/`, `scripts/`, `VERSION` und diese Anleitung.

## 2. In das Repository kopieren

```bash
cd ~/Downloads/TMBA-0.7.1-B-DummySource-PCM

cp -R . ~/Development/tmba/
```

## 3. Prüfskript kontrollieren und freigeben

```bash
ls -l ~/Development/tmba/scripts/check-dummy-source.sh

chmod +x ~/Development/tmba/scripts/check-dummy-source.sh
```

## 4. Tests starten

```bash
cd ~/Development/tmba

./scripts/check-dummy-source.sh
```

Erwartete Abschlussmeldung:

```text
TMBA v0.7.1-B erfolgreich geprüft.
```

## 5. GitHub aktualisieren

```bash
git status
git add .
git commit -m "Release v0.7.1-B: DummySource and PCM generator"
git push
git status
```
