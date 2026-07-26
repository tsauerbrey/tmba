# ADR-0017: Rootfs-Verkettung für die TMBA-pi-gen-Stage

## Status

Akzeptiert

## Kontext

`pi-gen` behandelt jede Stage als eigenes Build-Arbeitsverzeichnis. Das Root-Dateisystem einer vorherigen Stage wird nicht implizit in eine benutzerdefinierte Folgestage übernommen.

Ohne ein `prerun.sh` mit `copy_previous` versucht der Paket-Runner, in ein nicht vorhandenes `${ROOTFS_DIR}` zu wechseln. Der Build endet dann vor dem ersten TMBA-Paket mit `Unable to chroot/chdir`.

## Entscheidung

`stage-tmba` erhält ein eigenes `prerun.sh`. Existiert `${ROOTFS_DIR}` noch nicht, ruft es die von `pi-gen` bereitgestellte Funktion `copy_previous` auf.

## Folgen

- `stage-tmba` baut reproduzierbar auf dem vollständigen Ergebnis von `stage2` auf.
- Die originale `pi-gen`-Stage bleibt unverändert.
- Alle TMBA-Paket-, Datei-, Hardware- und Service-Schritte arbeiten auf demselben fortgeschriebenen Root-Dateisystem.
