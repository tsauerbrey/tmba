# ADR-0010: PCM-Writer als Grenze zwischen Quelle und Pipeline

## Status

Angenommen

## Entscheidung

PCM-liefernde Audioquellen erhalten eine einfache Callable-Schnittstelle
`writer(bytes) -> int`. Die Quelle kennt dadurch weder ALSA noch den konkreten
OutputDriver. `AudioPipeline.write()` übernimmt die Weiterleitung.

## Folgen

- Quellen bleiben unabhängig vom Ausgabegerät.
- DummySource, AirPlay-Adapter und Bluetooth-Adapter können denselben Vertrag nutzen.
- Unit-Tests können Writer ohne Hardware ersetzen.
- DSP-Verarbeitung kann später innerhalb der Pipeline ergänzt werden, ohne die
  Quellen-API zu ändern.
