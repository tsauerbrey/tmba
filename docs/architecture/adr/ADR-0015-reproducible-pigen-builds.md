# ADR-0015: Reproduzierbare und vorab geprüfte pi-gen-Builds

## Status

Akzeptiert

## Kontext

Ein vollständiger Raspberry-Pi-Image-Build benötigt viel Zeit und Speicher. Ein beweglicher Branch als alleinige Build-Abhängigkeit und fehlende Ressourcenprüfungen können zu nicht reproduzierbaren Ergebnissen oder späten Buildabbrüchen führen.

## Entscheidung

TMBA verwendet `pi-gen` als externe Build-Abhängigkeit im ignorierten lokalen Cache. Der verwendete Stand wird zusätzlich zum Branch durch einen vollständigen Git-Commit festgelegt. Vor jedem echten Build prüft ein Preflight-Skript Docker-Erreichbarkeit, ARM64-Ausführung, CPU, Arbeitsspeicher, freien Speicher, Werkzeuge und den Projektpfad.

Der Build erzeugt ein Zeitstempelprotokoll, Metadaten, Image-Artefakte und SHA-256-Prüfsummen. `--clean` entfernt ausschließlich Cache und generierte Artefakte.

## Konsequenzen

- Builds sind gegen spätere Änderungen des Remote-Branches abgesichert.
- Erkennbare Umgebungsprobleme werden vor dem langen Build gemeldet.
- Fehlerstatus des Docker-Builds geht trotz `tee` nicht verloren.
- `pi-gen` wird nicht als Git-Submodul im TMBA-Repository gespeichert.
- Ein Wechsel des `pi-gen`-Stands erfolgt bewusst durch Änderung des festgelegten Commits.
