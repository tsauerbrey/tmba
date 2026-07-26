# TMBA Installation

## v0.8.1 – Erstes bootfähiges TMBA-OS

### Lokale Prüfung

```bash
cd ~/Development/tmba
./scripts/check-image-builder.sh
./image-builder/build.sh --preflight
./image-builder/build.sh --prepare
```

### Vollständiges Image bauen

```bash
./image-builder/build.sh --build
```

Das Image, das Buildprotokoll, die Metadaten und die SHA-256-Prüfsummen werden unter `image-builder/dist/` abgelegt.

### Erster Start auf dem Raspberry Pi

```bash
ssh tmba@tmba.local
cat /etc/tmba-image-release
systemctl status tmba-backend --no-pager
systemctl status tmba-healthcheck --no-pager
curl http://127.0.0.1:8000/system/health
cat /var/log/tmba/boot.log
aplay -l
```

Das vorläufige Developer-Passwort ist `tmba`.

---

# TMBA v0.7.3-B – Installation und Prüfung

## Dateien in das Repository kopieren

Den Inhalt des Release-Archivs direkt nach `~/Development/tmba/` kopieren.

## Lokale Prüfung

```bash
cd ~/Development/tmba
chmod +x image-builder/build.sh image-builder/prepare-pigen.sh image-builder/validate.sh scripts/check-image-builder.sh
./scripts/check-image-builder.sh
```

## pi-gen vorbereiten

```bash
./image-builder/build.sh --prepare
```

Dabei wird `pi-gen` nach `image-builder/cache/pi-gen` geladen und eine TMBA-spezifische Konfiguration erzeugt. Es entsteht noch kein Image.

## Echtes Image bauen

Docker muss laufen. Außerdem sollten mindestens 35 GB freier Speicher verfügbar sein.

```bash
./image-builder/build.sh --build
```

Die Ausgabe liegt anschließend unter `image-builder/dist/`. Der Build kann je nach Internetverbindung und Rechner deutlich länger dauern.

## Sicherheit

Der Benutzer `tmba` erhält im Developer Image vorläufig das Passwort `tmba`. Nach dem ersten SSH-Login sofort ändern:

```bash
passwd
```

## v0.7.3-C – Image-Builder-Prüfung

```bash
./scripts/check-image-builder.sh
./image-builder/build.sh --preflight
./image-builder/build.sh --prepare
```

Erst wenn der Preflight erfolgreich ist, wird der vollständige Build mit `./image-builder/build.sh --build` gestartet. Cache und Artefakte lassen sich mit `./image-builder/build.sh --clean` entfernen.
