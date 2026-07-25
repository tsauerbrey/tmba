# TMBA-OS Architektur

Dieses Verzeichnis enthält die technische Dokumentation der TMBA-Architektur.

Geplante Dokumente:

- AudioManager
- SourceManager
- EventBus
- AudioPipeline
- CamillaDSP
- ALSA-Ausgabe
- Hardwareintegration
- Frontend-Backend-Kommunikation
- Start- und Abschaltablauf

## Zentrale Regel

Alle Audioquellen verwenden genau eine gemeinsame Audio-Pipeline.

```text
Audioquelle
    │
    ▼
AudioManager
    │
    ▼
AudioPipeline
    │
    ▼
DSP
    │
    ▼
Hardwareausgabe
```

Parallele, unkontrollierte Ausgabepfade sollen vermieden werden.
