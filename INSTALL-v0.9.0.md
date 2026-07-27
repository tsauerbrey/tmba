# TMBA v0.9.0 installieren und testen

## 1. Paket auf dem Mac einspielen

Sichere zuerst deinen aktuellen Stand:

```bash
cd ~/Development
cp -R tmba tmba-backup-0.8.4
```

Entpacke danach das Paket in `~/Development`. Die enthaltene Struktur beginnt mit dem Ordner `tmba/`.

## 2. Prüfungen ausführen

```bash
cd ~/Development/tmba
./image-builder/validate.sh
PYTHONPATH=backend python3 -m pytest \
  backend/tests/test_alsa_output.py \
  backend/tests/test_runtime_audio_config.py \
  backend/tests/test_output_factory.py \
  backend/tests/test_audio_pipeline.py \
  backend/tests/test_audio_manager.py \
  backend/tests/test_audio_manager_pipeline.py -q
python3 -m pytest image-builder/tests/test_builder.py -q
```

Erwartetes Ergebnis für die gezielten Backend-Tests: `48 passed`.

Erwartetes Ergebnis für den Builder: `21 passed`.

## 3. Neues Image bauen

```bash
cd ~/Development/tmba/image-builder
./build.sh
```

Das fertige Image liegt anschließend in:

```text
~/Development/tmba/image-builder/dist/
```

## 4. API auf dem Raspberry Pi kontrollieren

```bash
curl -s http://localhost:8000/audio/pipeline | python3 -m json.tool
```

Erwartet werden unter anderem:

```json
{
  "driver": "alsa",
  "device": "hw:CARD=sndrpihifiberry,DEV=0",
  "sample_rate": 48000,
  "channels": 2,
  "format": "S16_LE"
}
```

## 5. Testton über die REST-API

Der Testton ist absichtlich auf maximal 50 % digitale Amplitude und zehn Sekunden begrenzt. Beginne mit dem Standardwert von 20 %:

```bash
curl -s -X POST http://localhost:8000/audio/testtone \
  -H 'Content-Type: application/json' \
  -d '{
    "frequency_hz": 440,
    "duration_seconds": 3,
    "amplitude": 0.20
  }' | python3 -m json.tool
```

Der Ton muss auf beiden Lautsprechern gleichzeitig hörbar sein.

## 6. Wichtige Hardwarekonfiguration

In `/boot/firmware/config.txt` muss stehen:

```ini
dtoverlay=hifiberry-amp4pro
```

TMBA verwendet keine feste Kartennummer wie `hw:0,0`. Dadurch funktioniert die Ausgabe auch dann, wenn HDMI vor der HiFiBerry als Karte 0 und 1 registriert wird.
