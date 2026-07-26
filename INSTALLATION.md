# TMBA v0.7.0-B – Installation

## 1. Paket entpacken

```bash
cd ~/Downloads
unzip -o TMBA-0.7.0-B-Source-Arbitration.zip \
  -d TMBA-0.7.0-B-Source-Arbitration
```

## 2. Dateien in das Repository kopieren

Das ZIP enthält **keine zusätzliche Paket-Unterebene**. Direkt kopieren:

```bash
cd ~/Downloads/TMBA-0.7.0-B-Source-Arbitration
cp -R . ~/Development/tmba/
```

## 3. Prüfskript ausführen

```bash
chmod +x ~/Development/tmba/scripts/check-source-arbitration.sh
cd ~/Development/tmba
./scripts/check-source-arbitration.sh
```

Erwartete Abschlussmeldung:

```text
TMBA v0.7.0-B erfolgreich geprüft.
```

## 4. GitHub aktualisieren

```bash
git status
git add .
git commit -m "Release v0.7.0-B: source arbitration"
git push
git status
```
