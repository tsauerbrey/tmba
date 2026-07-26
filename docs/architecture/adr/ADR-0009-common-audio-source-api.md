# ADR-0009: Gemeinsame AudioSource-API

## Status

Akzeptiert für TMBA v0.7.1-A.

## Kontext

AirPlay, Bluetooth und Webradio besitzen unterschiedliche technische
Lebenszyklen. Die AudioEngine soll diese Unterschiede nicht direkt kennen.
Sie benötigt einen stabilen Vertrag für Verbindung, Wiedergabe und Status.

## Entscheidung

Alle künftigen Quellen implementieren `tmba.audio.sources.AudioSource`.
Der Vertrag definiert:

- `connect()` und `disconnect()`
- `start()` und `stop()`
- optional `pause()` und `resume()`
- `status()` mit einem normalisierten `SourceStatus`
- deklarative `SourceCapabilities`

`AudioSourceRegistry` verwaltet konkrete Implementierungen. Die bestehende
Prioritätsentscheidung bleibt ausschließlich in `SourceArbitrator` und
`AudioEngine`.

## Konsequenzen

- Neue Quellen sind unabhängig von der Engine testbar.
- Benutzeroberfläche und REST-API können einen gemeinsamen Status auswerten.
- Bestehende Dienste werden schrittweise über Adapter angebunden; v0.7.1-A
  verändert ihr Verhalten noch nicht.
