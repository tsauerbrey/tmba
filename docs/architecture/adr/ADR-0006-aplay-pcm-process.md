# ADR-0006: Persistenter aplay-Prozess als erster ALSA-PCM-Sink

## Status

Angenommen für TMBA v0.6.2-B.

## Entscheidung

TMBA verwendet zunächst einen persistenten `aplay`-Unterprozess. Rohes PCM
wird über `stdin` übertragen. Der Prozess wird beim Start des OutputDrivers
geöffnet und beim Stoppen kontrolliert beendet.

## Gründe

- keine zusätzliche native Python-Abhängigkeit
- auf Raspberry Pi OS und Debian über `alsa-utils` verfügbar
- klare Prozessgrenze für Fehlerbehandlung
- auf macOS vollständig mit Test-Doubles prüfbar
- später gegen eine direkte ALSA-Bibliothek austauschbar, ohne die
  AudioPipeline neu zu entwerfen

## Konsequenzen

`AlsaOutputDriver.write(bytes)` ist die erste produktive PCM-Schnittstelle.
Backpressure erfolgt über den blockierenden Pipe-Schreibvorgang. Eine
asynchrone Ringpuffer-Strategie ist ausdrücklich nicht Teil dieses
Meilensteins.
