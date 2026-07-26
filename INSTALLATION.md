# TMBA v0.7.2-B installieren

Dieses Paket wird über den bestehenden TMBA-Repository-Stand kopiert. Auf dem Mac werden zunächst nur Code, Tests und Deployment-Dateien geprüft. Die privilegierte AirPlay-Installation wird später direkt auf dem Raspberry Pi ausgeführt.

## 1. Paket in das Repository kopieren

```bash
cd ~/Downloads
unzip -o TMBA-0.7.2-B-AirPlay-Runtime.zip \
  -d TMBA-0.7.2-B-AirPlay-Runtime

cd ~/Downloads/TMBA-0.7.2-B-AirPlay-Runtime
cp -R . ~/Development/tmba/
```

## 2. Version und Prüfskript kontrollieren

```bash
cat ~/Development/tmba/VERSION
ls -l ~/Development/tmba/scripts/check-airplay-runtime.sh
```

Erwartete Version:

```text
0.7.2-B
```

## 3. Mac-Tests ausführen

```bash
chmod +x ~/Development/tmba/scripts/check-airplay-runtime.sh
cd ~/Development/tmba
./scripts/check-airplay-runtime.sh
```

## 4. GitHub aktualisieren

```bash
git status
git add .
git commit -m "Release v0.7.2-B: AirPlay runtime integration"
git push
git status
```

## 5. Später auf dem Raspberry Pi installieren

Das folgende Kommando erst ausführen, wenn das Repository auf dem Raspberry Pi vorhanden ist:

```bash
cd ~/tmba
sudo ./scripts/install-airplay-runtime.sh \
  "TMBA" \
  "hw:sndrpihifiberry" \
  "Digital" \
  "hw:sndrpihifiberry"
```

Danach prüfen:

```bash
systemctl status shairport-sync.service --no-pager
systemctl status avahi-daemon.service --no-pager
aplay -L
amixer scontrols
journalctl -u shairport-sync.service -n 100 --no-pager
```

Der Verstärker sollte beim ersten Hörtest auf eine niedrige Lautstärke eingestellt sein. Falls `aplay -L` oder `amixer scontrols` andere Namen ausgeben, werden die vier Parameter des Installationsskripts entsprechend angepasst.
