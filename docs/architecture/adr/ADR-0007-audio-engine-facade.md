# ADR-0007: AudioEngine als zentrale Fassade

## Status

Akzeptiert für TMBA v0.7.0-A.

## Kontext

AudioManager, SourceManager und AudioPipeline besitzen bereits klar abgegrenzte Aufgaben. REST und spätere Benutzeroberflächen sollten diese internen Komponenten jedoch nicht unabhängig voneinander steuern.

## Entscheidung

Eine `AudioEngine` wird als zentrale Anwendungsschnittstelle eingeführt. Sie:

- normiert Zustände und Statusdaten,
- koordiniert Start, Stopp und Quellenaktivierung,
- delegiert Transportbefehle an den AudioManager,
- veröffentlicht Lebenszyklusereignisse über den EventBus,
- verändert die bestehenden Verantwortlichkeiten von AudioManager und AudioPipeline nicht.

## Folgen

Neue externe Schnittstellen sollen bevorzugt die AudioEngine verwenden. Bestehende AudioManager-Endpunkte bleiben vorerst kompatibel und werden nicht entfernt.
