# ADR-0001: Eine gemeinsame AudioPipeline

- Status: Akzeptiert
- Datum: 2026-07-25
- Version: TMBA v0.6.1-A

## Kontext

TMBA unterstützt Webradio, Bluetooth und AirPlay. Ohne eine zentrale Pipeline
könnten Quellen unterschiedliche Lautstärke-, DSP- und Ausgabepfade verwenden.
Das würde Fehler, Inkonsistenzen und schwer wartbare Sonderfälle erzeugen.

## Entscheidung

Alle Quellen werden künftig über genau eine AudioPipeline geführt.

## Folgen

Positiv:

- einheitliche Lautstärke
- einheitliche DSP-Verarbeitung
- einheitlicher Limiter
- reproduzierbarer Signalweg
- einfachere Tests

Zu beachten:

- die Quellenumschaltung muss exklusiv bleiben
- der AudioManager wird in v0.6.1-B an die Pipeline angebunden
