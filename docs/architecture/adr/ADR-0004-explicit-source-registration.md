# ADR-0004: Explizite Registrierung der Standardquellen

- Status: Akzeptiert
- Datum: 2026-07-26
- Version: TMBA v0.6.1-C

## Kontext

Bisher wurde `register_default_sources()` beim Import von `tmba.audio.manager` ausgeführt. Dadurch importierten auch isolierte Tests automatisch AirPlay-, Bluetooth- und Webradio-Dienste sowie deren optionale Abhängigkeiten.

## Entscheidung

`manager.py` definiert weiterhin den Singleton und die Funktion `register_default_sources()`, führt die Funktion aber nicht mehr selbst aus. Die FastAPI-Anwendung ruft die Registrierung in `tmba.main` einmal explizit während des Anwendungsaufbaus auf.

## Folgen

- Der AudioManager kann isolierter importiert und getestet werden.
- Optionale Dienstabhängigkeiten werden nicht durch jeden Manager-Import geladen.
- Der Anwendungsstart bleibt nachvollziehbar.
