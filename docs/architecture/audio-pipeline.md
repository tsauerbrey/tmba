# TMBA AudioPipeline – Architektur v0.6.1-A

## Zweck

Die AudioPipeline bildet den gemeinsamen logischen Signalweg aller
TMBA-Audioquellen. In v0.6.1-A wird ausschließlich die Architektur modelliert.
Es werden noch keine realen Audiodaten verarbeitet und der bestehende
AudioManager wird noch nicht verändert.

## Signalweg

```text
AudioManager
    │
    ▼
AudioPipeline
    │
    ├── SourceGainStage
    ├── ReplayGainStage
    ├── LoudnessStage
    ├── EqualizerStage
    ├── LimiterStage
    └── OutputStage
            │
            ▼
       OutputDriver
            │
            └── NullOutputDriver
```

## Verantwortlichkeiten

### AudioPipeline

- verwaltet die Reihenfolge der Stufen
- validiert die Struktur
- verwaltet den Lebenszyklus
- liefert einen serialisierbaren Status
- hält die Pipeline-Konfiguration
- kennt nur die abstrakte OutputDriver-Schnittstelle

### PipelineStage

- besitzt einen eindeutigen Namen
- besitzt einen Typ
- kann vorbereitet, aktiviert, deaktiviert und zurückgesetzt werden
- liefert einen unveränderlichen Status-Schnappschuss

### OutputDriver

- kapselt das Ausgabeziel
- wird später durch einen ALSA-Treiber erweitert
- verhindert eine direkte ALSA-Abhängigkeit in der Pipeline

### NullOutputDriver

- öffnet kein Audiogerät
- eignet sich für macOS und automatisierte Tests
- simuliert Start, Betrieb und Stopp

## Architekturregeln

1. Eine Pipeline besitzt genau eine OutputStage.
2. Die OutputStage steht immer an letzter Stelle.
3. Stufennamen sind innerhalb einer Pipeline eindeutig.
4. Die OutputStage kann nicht deaktiviert werden.
5. Reale Hardware ist in v0.6.1-A nicht beteiligt.
6. Die Integration in AudioManager erfolgt erst in v0.6.1-B.
