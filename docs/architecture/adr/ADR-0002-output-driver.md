# ADR-0002: Ausgabe über OutputDriver abstrahieren

- Status: Akzeptiert
- Datum: 2026-07-25
- Version: TMBA v0.6.1-A

## Kontext

TMBA wird auf macOS entwickelt und später auf einem Raspberry Pi mit ALSA und
HiFiBerry betrieben. Eine direkte ALSA-Abhängigkeit in der AudioPipeline würde
Tests und Entwicklung auf dem Mac erschweren.

## Entscheidung

Die AudioPipeline verwendet ausschließlich die OutputDriver-Schnittstelle.

Der erste konkrete Treiber ist NullOutputDriver. Ein ALSAOutputDriver folgt in
einem späteren Meilenstein.

## Folgen

Positiv:

- sichere Simulation auf macOS
- keine Hardwarepflicht für Unit-Tests
- ALSA kann später ohne Umbau der Pipeline ergänzt werden
- alternative Ausgaben bleiben möglich
