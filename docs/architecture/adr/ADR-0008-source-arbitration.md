# ADR-0008: Prioritätsbasierte Quellen-Arbitration

## Status

Angenommen für TMBA v0.7.0-B.

## Kontext

AirPlay, Bluetooth und Webradio dürfen nicht gleichzeitig die zentrale AudioPipeline kontrollieren. Die Entscheidung über einen Quellenwechsel muss unabhängig von den konkreten Quelldiensten erfolgen.

## Entscheidung

Die AudioEngine verwendet einen eigenständigen `SourceArbitrator`. Die Standardprioritäten sind:

| Quelle | Priorität |
|---|---:|
| AirPlay | 30 |
| Bluetooth | 20 |
| Webradio | 10 |
| Keine Quelle | 0 |

Eine Quelle darf die aktive Quelle automatisch nur ersetzen, wenn ihre Priorität höher ist. `force=true` erlaubt einen bewussten manuellen Wechsel unabhängig von der Priorität. Die Auswahl `none` deaktiviert immer die aktuelle Quelle.

## Konsequenzen

- Prioritätsregeln sind zentral und separat testbar.
- Niedrig priorisierte Hintergrundquellen unterbrechen keine wichtige Wiedergabe.
- Die Benutzeroberfläche kann mit `force=true` weiterhin einen expliziten Quellenwechsel auslösen.
- Künftige Quellen können durch Erweiterung der Prioritätstabelle ergänzt werden.
