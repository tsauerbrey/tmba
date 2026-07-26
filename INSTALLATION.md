# Installation TMBA v0.6.1-C

## 1. ZIP entpacken und kopieren

```bash
cd ~/Downloads
unzip -o TMBA-0.6.1-C-Pipeline-REST-API.zip -d TMBA-0.6.1-C-Pipeline-REST-API
cd ~/Downloads/TMBA-0.6.1-C-Pipeline-REST-API
cp -R . ~/Development/tmba/
```

## 2. Skripte ausführbar machen

```bash
chmod +x ~/Development/tmba/scripts/check-audio-pipeline-api.sh
chmod +x ~/Development/tmba/scripts/move-default-source-registration.py
```

## 3. Import-time-Registrierung entfernen

```bash
cd ~/Development/tmba
python3 scripts/move-default-source-registration.py
```

## 4. Tests

```bash
./scripts/check-audio-pipeline-api.sh
```

## 5. Optional manuell testen

Terminal 1:

```bash
cd ~/Development/tmba/backend
source .venv/bin/activate
PYTHONPATH=. uvicorn tmba.main:app --reload
```

Terminal 2:

```bash
curl -s http://127.0.0.1:8000/audio/pipeline | python3 -m json.tool
```

## 6. Commit

```bash
cd ~/Development/tmba
git add .
git commit -m "Expose AudioPipeline status through REST API"
git push
```
