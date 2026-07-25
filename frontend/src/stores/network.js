import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  connectWifi,
  disconnectWifi,
  fetchNetworkStatus,
  fetchSavedWifiConnections,
  forgetWifi,
  scanWifiNetworks,
} from '../api/network'

export const useNetworkStore = defineStore('network', () => {
  const status = ref(null)
  const networks = ref([])
  const savedConnections = ref([])
  const loading = ref(false)
  const scanning = ref(false)
  const actionPending = ref(false)
  const errorMessage = ref('')
  const infoMessage = ref('')

  const wifi = computed(() => status.value?.wifi ?? {})
  const connected = computed(() => wifi.value.connected === true)
  const connectedSsid = computed(() => wifi.value.ssid ?? '')
  const wifiInterface = computed(() => wifi.value.interface ?? null)
  const localIp = computed(() => status.value?.local_ip ?? '–')
  const backend = computed(() => status.value?.backend ?? 'unbekannt')
  const wifiSupported = computed(
    () => wifi.value.supported !== false,
  )

  function clearMessages() {
    errorMessage.value = ''
    infoMessage.value = ''
  }

  function setResultMessage(result, fallback) {
    infoMessage.value = result?.message || fallback
  }

  async function loadStatus() {
    try {
      status.value = await fetchNetworkStatus()
    } catch (error) {
      errorMessage.value = error.message
    }
  }

  async function loadSavedConnections() {
    try {
      const result = await fetchSavedWifiConnections()
      savedConnections.value = result?.connections ?? []

      if (result?.supported === false && result?.message) {
        infoMessage.value = result.message
      }
    } catch (error) {
      errorMessage.value = error.message
    }
  }

  async function scan() {
    scanning.value = true
    clearMessages()

    try {
      const result = await scanWifiNetworks()
      networks.value = result?.networks ?? []

      if (result?.supported === false) {
        infoMessage.value =
          result.message
          || 'WLAN-Scan wird auf diesem System nicht unterstützt.'
      }
    } catch (error) {
      errorMessage.value = error.message
    } finally {
      scanning.value = false
    }
  }

  async function refreshAll() {
    loading.value = true
    clearMessages()

    try {
      await Promise.all([
        loadStatus(),
        loadSavedConnections(),
      ])

      await scan()
    } finally {
      loading.value = false
    }
  }

  async function connect({
    ssid,
    password = '',
    hidden = false,
  }) {
    actionPending.value = true
    clearMessages()

    try {
      const result = await connectWifi({
        ssid,
        password,
        hidden,
      })

      if (result?.success === false) {
        errorMessage.value =
          result.error
          || result.message
          || 'Die WLAN-Verbindung konnte nicht hergestellt werden.'

        return false
      }

      setResultMessage(result, `Mit ${ssid} verbunden.`)
      await Promise.all([
        loadStatus(),
        loadSavedConnections(),
      ])

      return true
    } catch (error) {
      errorMessage.value = error.message
      return false
    } finally {
      actionPending.value = false
    }
  }

  async function disconnect() {
    actionPending.value = true
    clearMessages()

    try {
      const result = await disconnectWifi(wifiInterface.value)

      if (result?.success === false) {
        errorMessage.value =
          result.error
          || result.message
          || 'Die WLAN-Verbindung konnte nicht getrennt werden.'

        return false
      }

      setResultMessage(result, 'WLAN-Verbindung getrennt.')
      await loadStatus()
      return true
    } catch (error) {
      errorMessage.value = error.message
      return false
    } finally {
      actionPending.value = false
    }
  }

  async function forget(connectionName) {
    actionPending.value = true
    clearMessages()

    try {
      const result = await forgetWifi(connectionName)

      if (result?.success === false) {
        errorMessage.value =
          result.error
          || result.message
          || 'Die gespeicherte Verbindung konnte nicht gelöscht werden.'

        return false
      }

      setResultMessage(
        result,
        `Gespeicherte Verbindung ${connectionName} gelöscht.`,
      )

      await loadSavedConnections()
      return true
    } catch (error) {
      errorMessage.value = error.message
      return false
    } finally {
      actionPending.value = false
    }
  }

  return {
    status,
    networks,
    savedConnections,
    loading,
    scanning,
    actionPending,
    errorMessage,
    infoMessage,
    wifi,
    connected,
    connectedSsid,
    wifiInterface,
    localIp,
    backend,
    wifiSupported,
    loadStatus,
    loadSavedConnections,
    scan,
    refreshAll,
    connect,
    disconnect,
    forget,
    clearMessages,
  }
})
