<script setup>
import {
  onMounted,
  onUnmounted,
  ref,
} from 'vue'
import { storeToRefs } from 'pinia'

import MainScreen from './components/MainScreen.vue'
import PlayerControls from './components/PlayerControls.vue'
import SourceDetails from './components/SourceDetails.vue'
import StatusBar from './components/StatusBar.vue'
import TrackInfo from './components/TrackInfo.vue'
import VolumeBar from './components/VolumeBar.vue'
import WebradioBrowser from './components/WebradioBrowser.vue'
import WifiSettings from './components/WifiSettings.vue'

import { usePlayerStore } from './stores/player'

const playerStore = usePlayerStore()

const {
  source,
  volume,
  title,
  artist,
  album,
  coverUrl,
  wifiConnected,
  bluetoothConnected,
  isLoading,
  errorMessage,
  isPlaying,
} = storeToRefs(playerStore)

const {
  loadStatus,
  setVolume,
  selectSource,
  play,
  pause,
  stop,
  previous,
  next,
} = playerStore

const webRadioBrowserOpen = ref(false)
const sourceDetailsOpen = ref(false)
const wifiSettingsOpen = ref(false)

let refreshTimer = null

function closeOverlays() {
  webRadioBrowserOpen.value = false
  sourceDetailsOpen.value = false
  wifiSettingsOpen.value = false
}

function handleCoverAction(selectedSource) {
  closeOverlays()

  if (selectedSource === 'webradio') {
    webRadioBrowserOpen.value = true
    return
  }

  if (
    selectedSource === 'airplay'
    || selectedSource === 'bluetooth'
    || selectedSource === 'usb'
  ) {
    sourceDetailsOpen.value = true
  }
}

function openWifiSettings() {
  closeOverlays()
  wifiSettingsOpen.value = true
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeOverlays()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)

  await loadStatus()

  refreshTimer = window.setInterval(() => {
    if (!playerStore.loading) {
      playerStore.refresh()
    }
  }, 1000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)

  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<template>
  <main class="app">
    <section class="player">
      <div class="status-wrapper">
        <StatusBar
          :volume="volume"
          :wifi-connected="wifiConnected"
          :bluetooth-connected="bluetoothConnected"
        />

        <button
          type="button"
          class="settings-button"
          aria-label="WLAN-Einstellungen öffnen"
          title="WLAN-Einstellungen"
          @click="openWifiSettings"
        >
          ⚙
        </button>
      </div>

      <MainScreen
        :source="source"
        :cover-url="coverUrl"
        :title="title"
        @select-source="selectSource"
        @activate-cover="handleCoverAction"
      />

      <div class="track-info-row">
        <TrackInfo
          :title="title"
          :artist="artist"
          :album="album"
        />
      </div>

      <section class="bottom-row">
        <PlayerControls
          :disabled="isLoading"
          :is-playing="isPlaying"
          @play="play"
          @pause="pause"
          @stop="stop"
          @previous="previous"
          @next="next"
        />

        <VolumeBar
          :volume="volume"
          :disabled="isLoading"
          @change="setVolume"
        />
      </section>

      <p
        v-if="errorMessage"
        class="error"
      >
        {{ errorMessage }}
      </p>
    </section>

    <WebradioBrowser
      v-if="webRadioBrowserOpen"
      @close="webRadioBrowserOpen = false"
    />

    <SourceDetails
      v-if="sourceDetailsOpen"
      :source="source"
      :title="title"
      :artist="artist"
      :album="album"
      :cover-url="coverUrl"
      :bluetooth-connected="bluetoothConnected"
      @close="sourceDetailsOpen = false"
    />

    <WifiSettings
      v-if="wifiSettingsOpen"
      @close="wifiSettingsOpen = false"
    />
  </main>
</template>

<style>
:root {
  font-family:
    Inter,
    Arial,
    Helvetica,
    sans-serif;
  color: #f5f5f5;
  background: #1f2023;
  color-scheme: dark;
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-width: 320px;
  min-height: 100%;
  margin: 0;
}

body {
  min-height: 100vh;
  overflow-x: hidden;
  background:
    radial-gradient(
      circle at center,
      #292c32 0%,
      #1b1d21 60%,
      #151619 100%
    );
}

button,
input {
  font: inherit;
}

button {
  touch-action: manipulation;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.app {
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.player {
  width: min(100%, 800px);
}

.status-wrapper {
  position: relative;
  padding-right: 52px;
}

.settings-button {
  position: absolute;
  top: 50%;
  right: 0;
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 12px;
  background: #343840;
  color: #fff;
  font-size: 22px;
  cursor: pointer;
  transform: translateY(-50%);
}

.settings-button:active {
  background: #474d57;
  transform: translateY(-50%) scale(0.96);
}

.track-info-row {
  min-width: 0;
}

.bottom-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: stretch;
  gap: 14px;
  margin-top: 12px;
}

.error {
  margin: 10px 0 0;
  padding: 12px;
  border: 1px solid rgb(255 120 120 / 20%);
  border-radius: 12px;
  background: #5a2323;
  color: #ffdede;
  text-align: center;
}

@media (max-width: 700px) {
  .bottom-row {
    gap: 10px;
  }
}

@media (max-height: 520px) {
  .app {
    align-items: flex-start;
    padding: 6px;
  }

  .status-wrapper {
    padding-right: 46px;
  }

  .settings-button {
    width: 40px;
    height: 40px;
  }

  .bottom-row {
    gap: 9px;
    margin-top: 7px;
  }

  .error {
    margin-top: 6px;
    padding: 8px;
    font-size: 13px;
  }
}
</style>
