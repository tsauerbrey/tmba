# ADR-0005: OutputDriver-Factory

- Status: Akzeptiert
- Datum: 2026-07-26
- Version: TMBA v0.6.2-A

## Kontext

Die AudioPipeline erzeugte bisher immer direkt einen `NullOutputDriver`.
Damit war die simulierte Entwicklung sicher, die Auswahl einer späteren
Hardwareausgabe aber in der Pipeline fest verdrahtet.

## Entscheidung

Eine zentrale Factory erzeugt den OutputDriver anhand von
`PipelineConfig.output.driver`.

Unterstützte Treiber:

- `null`
- `alsa`

Eine explizit injizierte Driver-Instanz hat weiterhin Vorrang. Dadurch bleiben
Unit-Tests vollständig kontrollierbar.

## Folgen

- Die Pipeline kennt keine konkrete Hardwareimplementierung mehr.
- Die Standardkonfiguration bleibt auf macOS sicher bei `null`.
- ALSA kann unter Linux vorbereitet werden, ohne Tests auf dem Mac zu öffnen.
- CamillaDSP kann später als weiterer Factory-Treiber ergänzt werden.
