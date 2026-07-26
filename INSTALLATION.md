# Installation TMBA v0.7.2-A

```bash
cd ~/Downloads
unzip -o TMBA-0.7.2-A-ServiceSource-AirPlay.zip \
  -d TMBA-0.7.2-A-ServiceSource-AirPlay
cd ~/Downloads/TMBA-0.7.2-A-ServiceSource-AirPlay
cp -R . ~/Development/tmba/
chmod +x ~/Development/tmba/scripts/check-service-source.sh
cd ~/Development/tmba
./scripts/check-service-source.sh
```

Bei Erfolg:

```bash
git status
git add .
git commit -m "Release v0.7.2-A: ServiceSource framework and AirPlay adapter"
git push
git status
```
