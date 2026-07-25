# ADR-0003: AudioManager steuert den Pipeline-Lebenszyklus

- Status: Akzeptiert
- Datum: 2026-07-25
- Version: TMBA v0.6.1-B

## Kontext

Audioquellen und AudioPipeline besitzen getrennte Lebenszyklen. Ohne zentrale
Koordination könnte eine Quelle spielen, während die Pipeline gestoppt ist,
oder die Pipeline nach dem Stoppen einer Quelle weiterlaufen.

## Entscheidung

Der AudioManager ist die einzige Komponente, die den Lebenszyklus der
AudioPipeline im normalen Betrieb steuert.

- Erfolgreiches `play` startet die Pipeline.
- `stop` stoppt Quelle und Pipeline.
- Ein Quellenwechsel stoppt die vorherige Quelle und die Pipeline.
- Ein fehlgeschlagener Pipeline-Start stoppt die gerade gestartete Quelle
  wieder.
- Pipelinefehler versetzen den AudioManager in den Zustand `error`.

## Folgen

Positiv:

- Quelle und Pipeline bleiben synchron.
- Fehler werden zentral behandelt.
- Der spätere ALSA- und CamillaDSP-Lebenszyklus erhält eine klare Zuständigkeit.

Zu beachten:

- Die Pipeline verarbeitet in v0.6.1-B weiterhin keine Audiodaten.
- REST-Zugriff auf den Pipeline-Status folgt erst in v0.6.1-C.
