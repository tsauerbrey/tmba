# ADR-0013: Deklarativer Developer Image Builder

## Status

Akzeptiert

## Kontext

TMBA benötigt eine reproduzierbare Zielplattform für Raspberry Pi 4, ARM64 und Raspberry Pi OS Lite. Direkte, manuelle Installationen auf einzelnen SD-Karten sind schwer nachvollziehbar und nicht zuverlässig wiederholbar.

## Entscheidung

Der Image Builder wird als eigener Repository-Bereich eingeführt. Zielparameter, Paketlisten, Dienste, Buildstufen und Overlays werden deklarativ versioniert. v0.7.3-A erlaubt ausschließlich Validierung und Dry-Run; ein echter Image-Build bleibt absichtlich gesperrt, bis Basisimage, Prüfsummen und privilegierte Buildumgebung festgelegt sind.

## Konsequenzen

- Änderungen am Zielsystem werden reviewbar und testbar.
- macOS kann Struktur und Buildplan prüfen, ohne Linux-Imagewerkzeuge auszuführen.
- GitHub Actions validiert den Builder unabhängig vom Backend.
- Der echte Image-Build kann später kontrolliert ergänzt werden.
