# Installation TMBA v0.6.2-A1

## 1. Paket entpacken und kopieren

```bash
cd ~/Downloads

unzip -o TMBA-0.6.2-A1-ALSA-Parser-Hotfix.zip \
  -d TMBA-0.6.2-A1-ALSA-Parser-Hotfix

cd ~/Downloads/TMBA-0.6.2-A1-ALSA-Parser-Hotfix

cp -R . ~/Development/tmba/
```

## 2. Prüfskript ausführbar machen

```bash
chmod +x \
  ~/Development/tmba/scripts/check-alsa-parser-hotfix.sh
```

## 3. Hotfix testen

```bash
cd ~/Development/tmba

./scripts/check-alsa-parser-hotfix.sh
```

Erwartete Abschlussmeldung:

```text
TMBA v0.6.2-A1 erfolgreich geprüft.
```

## 4. Commit und Push

Wenn alle Tests grün sind:

```bash
git add .
git commit -m "Fix ALSA device list parser"
git push
```

Der ursprüngliche Commit für v0.6.2-A kann zusammen mit diesem Hotfix bestehen
bleiben. Ein Zurücksetzen ist nicht notwendig.
