# Installation des Project Foundation Packs

## 1. Sicherung des aktuellen Standes

Im Projektordner:

```bash
cd ~/Development/tmba
git status
```

## 2. Paket kopieren

Der Inhalt dieses Pakets wird in den Projektordner kopiert:

```bash
cp -R . ~/Development/tmba/
```

Bestehende gleichnamige Dokumentationsdateien werden dabei ersetzt.

## 3. Prüfskript ausführbar machen

```bash
chmod +x ~/Development/tmba/scripts/check-release.sh
```

## 4. Änderungen kontrollieren

```bash
cd ~/Development/tmba
git status
git diff
```

## 5. Tests ausführen

```bash
./scripts/check-release.sh
```

## 6. Commit erstellen

```bash
git add .
git commit -m "Prepare TMBA v0.6.0 project foundation"
```

## 7. Hauptbranch zu GitHub übertragen

Zunächst den aktuellen Branchnamen prüfen:

```bash
git branch --show-current
```

Danach:

```bash
git push
```

Falls der Branch noch keinen Upstream besitzt:

```bash
git push -u origin main
```

## 8. Tag erstellen

```bash
git tag -a v0.6.0 -m "TMBA-OS v0.6.0"
git push origin v0.6.0
```

## Hinweis zur Lizenz

Im Paket ist bewusst noch keine Open-Source-Lizenz enthalten. Die Entscheidung
zwischen MIT, GPL oder einer anderen Lizenz sollte bewusst getroffen werden,
bevor das Projekt öffentlich veröffentlicht oder von anderen weiterverwendet
wird.
