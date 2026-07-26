# AudioPipeline REST API

## Endpunkt

```http
GET /audio/pipeline
```

Der Endpunkt liefert den schreibgeschützten Zustand der logischen
TMBA-AudioPipeline.

## Erfolgreiche Antwort

HTTP-Status:

```text
200 OK
```

Beispielstruktur:

```json
{
  "state": "created",
  "stage_count": 6,
  "enabled_stage_count": 3,
  "output": {
    "driver": "null",
    "state": "stopped",
    "device": "simulation",
    "sample_rate": 48000,
    "channels": 2,
    "format": "S32_LE",
    "details": {
      "simulation": true
    }
  },
  "stages": [],
  "config": {}
}
```

## Felder

### `state`

Lebenszykluszustand der gesamten Pipeline:

- `created`
- `ready`
- `running`
- `stopped`
- `error`

### `stage_count`

Gesamtzahl der Pipeline-Stufen.

### `enabled_stage_count`

Anzahl der Stufen mit `enabled: true`.

### `output`

Status des aktuellen OutputDrivers. In TMBA v0.6.1 ist dies standardmäßig der
`NullOutputDriver` mit dem Gerät `simulation`.

### `stages`

Geordnete Liste der Pipeline-Stufen:

1. `source_gain`
2. `replay_gain`
3. `loudness`
4. `equalizer`
5. `limiter`
6. `output`

Die Output-Stufe muss genau einmal vorkommen und immer die letzte Stufe sein.

### `config`

Wirksame Pipeline-Konfiguration, gegliedert nach Stufen.

## Fehlerantwort

Kann der Status nicht gelesen werden:

```text
503 Service Unavailable
```

Beispiel:

```json
{
  "detail": {
    "success": false,
    "error": "Der Status der AudioPipeline konnte nicht gelesen werden: ..."
  }
}
```

## Umfang von v0.6.1

Der Endpunkt ist ausschließlich lesend. Änderungen an DSP-Stufen,
Konfiguration oder OutputDriver sind noch nicht Bestandteil dieser Version.
