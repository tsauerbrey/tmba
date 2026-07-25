const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL
  ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  })

  let payload = null

  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const message =
      payload?.detail
      ?? payload?.error
      ?? payload?.message
      ?? `Netzwerkfehler (${response.status})`

    throw new Error(message)
  }

  return payload
}

export function fetchNetworkStatus() {
  return request('/network/status')
}

export function scanWifiNetworks() {
  return request('/network/wifi/scan')
}

export function fetchSavedWifiConnections() {
  return request('/network/wifi/saved')
}

export function connectWifi({
  ssid,
  password = null,
  hidden = false,
}) {
  return request('/network/wifi/connect', {
    method: 'POST',
    body: JSON.stringify({
      ssid,
      password: password || null,
      hidden,
    }),
  })
}

export function disconnectWifi(interfaceName = null) {
  return request('/network/wifi/disconnect', {
    method: 'POST',
    body: JSON.stringify({
      interface: interfaceName,
    }),
  })
}

export function forgetWifi(connection) {
  return request('/network/wifi/forget', {
    method: 'POST',
    body: JSON.stringify({
      connection,
    }),
  })
}
