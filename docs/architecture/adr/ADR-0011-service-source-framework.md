# ADR-0011: ServiceSource-Framework

## Status
Angenommen

## Kontext
AirPlay, Bluetooth und weitere Quellen werden durch externe Linux-Dienste bereitgestellt. Die AudioEngine darf keine systemd-spezifischen Befehle kennen.

## Entscheidung
`ServiceSource` bildet den gemeinsamen AudioSource-Lebenszyklus ab. Ein injizierbarer `ServiceController` kapselt `systemctl`. `AirPlaySource` ist der erste konkrete Adapter und verwendet standardmäßig `shairport-sync.service`.

Das Starten des Dienstes bedeutet, dass die Quelle empfangsbereit ist. Es bedeutet noch nicht, dass bereits ein externer Stream wiedergegeben wird. Diese Unterscheidung wird in einem späteren Meilenstein über shairport-sync-Hooks ergänzt.

## Folgen
- Systemdienstlogik ist auf macOS vollständig testbar.
- Die AudioEngine bleibt unabhängig von systemd.
- Bluetooth und weitere Dienste können denselben Unterbau verwenden.
- Für Schreiboperationen benötigt der spätere TMBA-Systemdienst passende systemd-/Polkit-Rechte.
