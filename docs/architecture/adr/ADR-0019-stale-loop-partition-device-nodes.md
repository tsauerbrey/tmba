# ADR-0019: Veraltete Loop-Partitionsgeräte vor dem Image-Export ersetzen

## Status

Angenommen – TMBA v0.8.4

## Kontext

Der pi-gen-Export erzeugt ein Loop-Gerät mit zwei Partitionen und legt fehlende
Partitionsknoten unter `/dev` mit `mknod` an. In lang laufenden Docker-VMs wie
OrbStack können dort jedoch noch Blockgeräte eines früheren Loop-Mappings
vorhanden sein. Der bisherige pi-gen-Test `-b` erkennt nur, dass ein Blockgerät
existiert, nicht ob dessen Major-/Minor-Nummern noch zum aktuellen Mapping
passen. `mkdosfs` kann dann mit `Operation not permitted` abbrechen.

## Entscheidung

TMBA wendet beim Vorbereiten des gepinnten pi-gen-Checkouts einen kleinen,
versionierten Patch auf `scripts/common` an. `ensure_loopdev_partitions` liest
die erwarteten Major-/Minor-Nummern aus `lsblk`, vergleicht sie mit den
vorhandenen Geräteknoten und ersetzt veraltete Knoten vor dem Formatieren.

Der Patch wird nur angewendet, wenn er exakt zum gepinnten pi-gen-Commit passt.
Andernfalls bricht die Vorbereitung mit einer klaren Fehlermeldung ab.

## Folgen

- Wiederholte Builds in OrbStack können denselben `/dev`-Namensraum sicher
  weiterverwenden.
- Das Raspberry-Pi-Partitionslayout bleibt unverändert.
- Der Eingriff ist klein, nachvollziehbar und an den pi-gen-Commit gekoppelt.
- Bei einem späteren pi-gen-Update muss der Patch erneut geprüft werden.
