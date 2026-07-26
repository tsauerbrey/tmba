# Installation TMBA v0.6.2-B

## 1. Paket installieren

```bash
cd ~/Downloads

unzip -o TMBA-0.6.2-B-ALSA-PCM-Streaming.zip \
  -d TMBA-0.6.2-B-ALSA-PCM-Streaming

cd ~/Downloads/TMBA-0.6.2-B-ALSA-PCM-Streaming
cp -R . ~/Development/tmba/
```

## 2. Prüfskript ausführbar machen

```bash
chmod +x \
  ~/Development/tmba/scripts/check-alsa-pcm-streaming.sh
```

## 3. Tests ausführen

```bash
cd ~/Development/tmba
./scripts/check-alsa-pcm-streaming.sh
```

Erwartete Abschlussmeldung:

```text
TMBA v0.6.2-B erfolgreich geprüft.
```

## 4. Commit und Push

```bash
git add .
git commit -m "Add ALSA PCM streaming output"
git push
```

## Raspberry-Pi-Hinweis

Auf dem späteren Zielsystem muss `aplay` vorhanden sein:

```bash
sudo apt install alsa-utils
```

Die Hardwareprüfung auf dem Raspberry Pi erfolgt separat, nachdem dieses
Paket lokal und in GitHub erfolgreich getestet wurde.
