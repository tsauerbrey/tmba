const API_BASE_URL = "http://localhost:8000"


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
      detail = errorData.detail || detail
    } catch {
      // Antwort enthält kein JSON.
    }

    throw new Error(detail)
  }

  return response.json()
}


export function getStatus() {
  return request("/status")
}


export function updateVolume(volume) {
  return request("/volume", {
    method: "POST",
    body: JSON.stringify({ volume }),
  })
}


export function selectSource(source) {
  return request("/source", {
    method: "POST",
    body: JSON.stringify({ source }),
  })
}


export function refreshPlayer() {
  return request("/player/refresh", {
    method: "POST",
  })
}


export function playPlayer() {
  return request("/player/play", {
    method: "POST",
  })
}


export function pausePlayer() {
  return request("/player/pause", {
    method: "POST",
  })
}


export function stopPlayer() {
  return request("/player/stop", {
    method: "POST",
  })
}


export function previousPlayer() {
  return request("/player/previous", {
    method: "POST",
  })
}


export function nextPlayer() {
  return request("/player/next", {
    method: "POST",
  })
}