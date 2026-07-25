<script setup>
import {
  computed,
  onMounted,
  onUnmounted,
  ref,
} from 'vue'
import { storeToRefs } from 'pinia'

import WifiDialog from './WifiDialog.vue'
import WifiSignal from './WifiSignal.vue'
import { useNetworkStore } from '../stores/network'

const emit = defineEmits(['close'])

const networkStore = useNetworkStore()

const {
  networks,
  savedConnections,
  loading,
  scanning,
  actionPending,
  errorMessage,
  infoMessage,
  connected,
  connectedSsid,
  localIp,
  backend,
} = storeToRefs(networkStore)

const selectedNetwork = ref(null)
let statusTimer = null

const visibleNetworks = computed(() => {
  return [...networks.value].sort((left, right) => {
    if (left.connected !== right.connected) {
      return left.connected ? -1 : 1
    }

    return (
      (right.signal_percent ?? 0)
      - (left.signal_percent ?? 0)
    )
  })
})

function isSaved(ssid) {
  return savedConnections.value.some(
    (connection) => connection.name === ssid,
  )
}

async function connect(payload) {
  const success = await networkStore.connect(payload)

  if (success) {
    selectedNetwork.value = null
    await networkStore.scan()
  }
}

async function disconnect() {
  await networkStore.disconnect()
  await networkStore.scan()
}

async function forget(connectionName) {
  await networkStore.forget(connectionName)
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    if (selectedNetwork.value) {
      selectedNetwork.value = null
      return
    }

    emit('close')
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  await networkStore.refreshAll()

  statusTimer = window.setInterval(() => {
    if (!networkStore.actionPending) {
      networkStore.loadStatus()
    }
  }, 5000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)

  if (statusTimer !== null) {
    window.clearInterval(statusTimer)
  }

  networkStore.clearMessages()
})
</script>

<template>
  <div class="settings-backdrop">
    <section class="wifi-settings">
      <header class="settings-header">
        <div>
          <p class="eyebrow">
            TMBA Einstellungen
          </p>
          <h1>WLAN</h1>
        </div>

        <button
          type="button"
          class="close-button"
          aria-label="WLAN-Einstellungen schließen"
          @click="$emit('close')"
        >
          ×
        </button>
      </header>

      <section class="status-card">
        <div class="status-main">
          <span
            class="status-dot"
            :class="{ online: connected }"
          />

          <div>
            <strong>
              {{
                connected
                  ? connectedSsid || 'WLAN verbunden'
                  : 'Nicht verbunden'
              }}
            </strong>

            <small>
              IP {{ localIp }} · {{ backend }}
            </small>
          </div>
        </div>

        <button
          v-if="connected"
          type="button"
          class="danger-button"
          :disabled="actionPending"
          @click="disconnect"
        >
          Trennen
        </button>
      </section>

      <div class="toolbar">
        <h2>Verfügbare Netzwerke</h2>

        <button
          type="button"
          class="refresh-button"
          :disabled="scanning || loading"
          @click="networkStore.scan"
        >
          {{ scanning ? 'Suche …' : '↻ Aktualisieren' }}
        </button>
      </div>

      <p
        v-if="errorMessage"
        class="message error-message"
      >
        {{ errorMessage }}
      </p>

      <p
        v-else-if="infoMessage"
        class="message info-message"
      >
        {{ infoMessage }}
      </p>

      <section class="network-list">
        <button
          v-for="network in visibleNetworks"
          :key="`${network.ssid}-${network.security}`"
          type="button"
          class="network-row"
          :class="{ connected: network.connected }"
          :disabled="actionPending"
          @click="selectedNetwork = network"
        >
          <WifiSignal :signal="network.signal_percent" />

          <span class="network-details">
            <strong>{{ network.ssid }}</strong>

            <small>
              {{ network.security || 'Offen' }}
              <template v-if="isSaved(network.ssid)">
                · gespeichert
              </template>
            </small>
          </span>

          <span
            v-if="network.connected"
            class="connected-label"
          >
            Verbunden
          </span>

          <span
            v-else
            class="chevron"
          >
            ›
          </span>
        </button>

        <div
          v-if="!visibleNetworks.length && !scanning"
          class="empty-state"
        >
          <strong>Keine WLAN-Netzwerke angezeigt</strong>
          <span>
            Auf macOS ist der Scan deaktiviert. Auf dem Raspberry
            werden die Netzwerke über NetworkManager angezeigt.
          </span>
        </div>
      </section>

      <section
        v-if="savedConnections.length"
        class="saved-section"
      >
        <h2>Gespeicherte Verbindungen</h2>

        <div class="saved-list">
          <div
            v-for="connection in savedConnections"
            :key="connection.uuid"
            class="saved-row"
          >
            <span>
              <strong>{{ connection.name }}</strong>
              <small v-if="connection.active">aktiv</small>
            </span>

            <button
              type="button"
              class="forget-button"
              :disabled="actionPending || connection.active"
              @click="forget(connection.name)"
            >
              Vergessen
            </button>
          </div>
        </div>
      </section>
    </section>

    <WifiDialog
      v-if="selectedNetwork"
      :network="selectedNetwork"
      :pending="actionPending"
      @close="selectedNetwork = null"
      @connect="connect"
    />
  </div>
</template>

<style scoped>
.settings-backdrop {
  position: fixed;
  z-index: 20;
  inset: 0;
  overflow-y: auto;
  background:
    radial-gradient(
      circle at top,
      #30343c 0%,
      #1b1d21 62%,
      #141518 100%
    );
}

.wifi-settings {
  width: min(800px, 100%);
  min-height: 100%;
  margin: 0 auto;
  padding: 12px;
}

.settings-header,
.status-card,
.toolbar,
.status-main,
.saved-row {
  display: flex;
  align-items: center;
}

.settings-header,
.status-card,
.toolbar,
.saved-row {
  justify-content: space-between;
}

.settings-header {
  gap: 12px;
}

.eyebrow {
  margin: 0 0 2px;
  color: #80c43b;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
}

h1 {
  font-size: 28px;
}

h2 {
  font-size: 17px;
}

.close-button {
  width: 46px;
  height: 46px;
  border: 0;
  border-radius: 50%;
  background: #383c45;
  color: #fff;
  font-size: 30px;
  cursor: pointer;
}

.status-card {
  gap: 12px;
  margin-top: 10px;
  padding: 12px 14px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 14px;
  background: rgb(255 255 255 / 5%);
}

.status-main {
  min-width: 0;
  gap: 10px;
}

.status-main strong,
.status-main small {
  display: block;
}

.status-main strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-main small {
  margin-top: 3px;
  color: #aeb5c0;
}

.status-dot {
  width: 13px;
  height: 13px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #737984;
  box-shadow: 0 0 0 4px rgb(115 121 132 / 15%);
}

.status-dot.online {
  background: #80c43b;
  box-shadow: 0 0 0 4px rgb(128 196 59 / 16%);
}

.toolbar {
  margin-top: 12px;
}

.refresh-button,
.danger-button,
.forget-button {
  min-height: 40px;
  padding: 0 14px;
  border: 0;
  border-radius: 10px;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.refresh-button {
  background: #3b414b;
}

.danger-button,
.forget-button {
  background: #6b2c2c;
}

.message {
  margin: 8px 0 0;
  padding: 8px 10px;
  border-radius: 9px;
  font-size: 13px;
}

.error-message {
  background: #5a2323;
  color: #ffdede;
}

.info-message {
  background: #283c4d;
  color: #d8efff;
}

.network-list {
  display: grid;
  gap: 7px;
  margin-top: 9px;
}

.network-row {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  min-height: 58px;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border: 1px solid rgb(255 255 255 / 9%);
  border-radius: 12px;
  background: #292d34;
  color: #fff;
  text-align: left;
  cursor: pointer;
}

.network-row.connected {
  border-color: rgb(128 196 59 / 50%);
  background: #283520;
}

.network-details {
  min-width: 0;
}

.network-details strong,
.network-details small {
  display: block;
}

.network-details strong {
  overflow: hidden;
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.network-details small {
  margin-top: 3px;
  color: #aeb5c0;
  font-size: 12px;
}

.connected-label {
  color: #a8df75;
  font-size: 12px;
  font-weight: 800;
}

.chevron {
  color: #aeb5c0;
  font-size: 28px;
}

.empty-state {
  display: grid;
  gap: 5px;
  padding: 18px;
  border: 1px dashed rgb(255 255 255 / 16%);
  border-radius: 12px;
  color: #b9c0ca;
  text-align: center;
}

.empty-state strong {
  color: #fff;
}

.empty-state span {
  font-size: 13px;
}

.saved-section {
  margin-top: 13px;
  padding-bottom: 10px;
}

.saved-list {
  display: grid;
  gap: 7px;
  margin-top: 8px;
}

.saved-row {
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgb(255 255 255 / 5%);
}

.saved-row span {
  min-width: 0;
}

.saved-row strong,
.saved-row small {
  display: block;
}

.saved-row small {
  margin-top: 2px;
  color: #80c43b;
  font-size: 12px;
}

@media (max-height: 520px) {
  .wifi-settings {
    padding: 8px 10px;
  }

  .status-card {
    margin-top: 6px;
    padding: 8px 12px;
  }

  .toolbar {
    margin-top: 8px;
  }

  .network-list {
    gap: 5px;
    margin-top: 6px;
  }

  .network-row {
    min-height: 51px;
    padding: 5px 10px;
  }

  .saved-section {
    margin-top: 9px;
  }
}
</style>
