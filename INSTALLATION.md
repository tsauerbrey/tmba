# TMBA v0.7.3-A installieren

Dieses Paket ergänzt das Repository um den Developer Image Builder. Es erzeugt noch kein bootfähiges Image und benötigt auf dem Mac keine privilegierten Befehle.

## 1. Paket kopieren

```bash
cd ~/Downloads
unzip -o TMBA-0.7.3-A-Developer-Image-Builder.zip \
  -d TMBA-0.7.3-A-Developer-Image-Builder

cd ~/Downloads/TMBA-0.7.3-A-Developer-Image-Builder
cp -R . ~/Development/tmba/
```

## 2. Version kontrollieren

```bash
cat ~/Development/tmba/VERSION
ls -l ~/Development/tmba/scripts/check-image-builder.sh
```

Erwartet: `0.7.3-A`.

## 3. Prüfung starten

```bash
chmod +x ~/Development/tmba/scripts/check-image-builder.sh
cd ~/Development/tmba
./scripts/check-image-builder.sh
```

## 4. GitHub aktualisieren

```bash
git status
git add .
git commit -m "Release v0.7.3-A: Developer Image Builder"
git push
git status
```
