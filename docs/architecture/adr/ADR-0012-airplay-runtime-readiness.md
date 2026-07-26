# ADR-0012: AirPlay-Laufzeit wird vor dem Dienststart geprüft

## Status

Angenommen für TMBA v0.7.2-B.

## Kontext

`AirPlaySource` steuert seit v0.7.2-A einen externen systemd-Dienst. Ein erfolgreicher `systemctl start` allein beweist jedoch nicht, dass der Host tatsächlich AirPlay wiedergeben kann. Dafür müssen mindestens das Programm `shairport-sync`, die Konfiguration, der systemd-Dienst, Avahi und das konfigurierte ALSA-Gerät verfügbar sein.

Direkte Host-Abfragen in der AudioEngine würden die Engine an Linux, systemd und ALSA koppeln. Sie wären außerdem auf macOS kaum testbar.

## Entscheidung

TMBA führt eine eigenständige, injizierbare Laufzeitgrenze ein:

- `AirPlayRuntimeConfig` beschreibt Empfängername, ALSA-Ausgabe, Mixer und Pfade.
- `AirPlayRuntimeInspector` prüft Voraussetzungen ohne das System zu verändern.
- `AirPlayRuntimeReport` liefert einen normalisierten Bereitschaftsstatus.
- `AirPlaySource.start()` verweigert den Start, solange der Laufzeitbericht nicht bereit ist.
- Ein separates Installationsskript übernimmt die privilegierte Host-Konfiguration.

## Konsequenzen

Die AudioEngine bleibt unabhängig von Linux-Kommandos. Laufzeitprüfungen lassen sich vollständig mit Testdoubles testen. Fehlende Voraussetzungen werden vor dem Dienststart sichtbar. Die tatsächliche Audioausgabe bleibt dennoch ein Hardware-Integrationstest auf dem Raspberry Pi.
