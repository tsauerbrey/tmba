const API_BASE_URL = "/api"


async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    let detail = `HTTP-Fehler ${response.status}`

    try {
      const errorData = await response.json()

      if (typeof errorData.detail === "string") {
        detail = errorData.detail
      } else if (
        errorData.detail
        && typeof errorData.detail === "object"
      ) {
        detail =
          errorData.detail.error
          || errorData.detail.message
          || detail
      }
    } catch {
      // Die Antwort enthält kein gültiges JSON.
    }

    throw new Error(detail)
  }

  return response.json()
}


export function getWebradioStations({
  favoritesOnly = false,
} = {}) {
  const parameters = new URLSearchParams()

  if (favoritesOnly) {
    parameters.set("favorites_only", "true")
  }

  const query = parameters.toString()

  return request(
    `/webradio/stations${query ? `?${query}` : ""}`,
  )
}


export function playWebradioStation(stationId) {
  return request(
    `/webradio/stations/${encodeURIComponent(stationId)}/play`,
    {
      method: "POST",
    },
  )
}


export function deleteWebradioStation(stationId) {
  return request(
    `/webradio/stations/${encodeURIComponent(stationId)}`,
    {
      method: "DELETE",
    },
  )
}


export function playOnlineWebradioStation(station) {
  return request("/webradio/play-station", {
    method: "POST",
    body: JSON.stringify({
      url: station.stream_url,
      station_name: station.name,
    }),
  })
}


export function setWebradioFavorite(
  stationId,
  favorite,
) {
  return request(
    `/webradio/stations/${encodeURIComponent(stationId)}/favorite`,
    {
      method: "POST",
      body: JSON.stringify({
        favorite,
      }),
    },
  )
}


export function searchOnlineWebradioStations({
  query = "",
  countryCode = "",
  tag = "",
  language = "",
  minimumBitrate = 0,
  limit = 30,
} = {}) {
  const parameters = new URLSearchParams()

  if (query.trim()) {
    parameters.set("q", query.trim())
  }

  if (countryCode.trim()) {
    parameters.set(
      "country_code",
      countryCode.trim().toUpperCase(),
    )
  }

  if (tag.trim()) {
    parameters.set("tag", tag.trim())
  }

  if (language.trim()) {
    parameters.set("language", language.trim())
  }

  if (Number(minimumBitrate) > 0) {
    parameters.set(
      "minimum_bitrate",
      String(Number(minimumBitrate)),
    )
  }

  parameters.set(
    "limit",
    String(
      Math.max(
        1,
        Math.min(100, Number(limit) || 30),
      ),
    ),
  )

  return request(
    `/webradio/online/search?${parameters.toString()}`,
  )
}


export function importOnlineWebradioStation(
  stationUuid,
  favorite = false,
) {
  return request(
    "/webradio/online/stations/import",
    {
      method: "POST",
      body: JSON.stringify({
        station_uuid: stationUuid,
        favorite,
      }),
    },
  )
}