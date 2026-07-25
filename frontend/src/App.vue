<script setup>
import { onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'

import MainScreen from './components/MainScreen.vue'
import StatusBar from './components/StatusBar.vue'
import VolumeBar from './components/VolumeBar.vue'
import TrackInfo from './components/TrackInfo.vue'
import PlayerControls from './components/PlayerControls.vue'
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


let refreshTimer = null

onMounted(async () => {
  await loadStatus()

  refreshTimer = window.setInterval(() => {
    if (!playerStore.loading) {
      playerStore.refresh()
    }
  }, 1000)
})

onUnmounted(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
  }
})
</script>

<template>
  <main class="app">
    <section class="player">
      <StatusBar
        :volume="volume"
        :wifi-connected="wifiConnected"
        :bluetooth-connected="bluetoothConnected"
      />

      <MainScreen
        :source="source"
        :cover-url="coverUrl"
        :title="title"
        @select-source="selectSource"
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

      <p v-if="errorMessage" class="error">
        {{ errorMessage }}
      </p>
    </section>
  </main>
</template>

<style>
:root {
  font-family: Inter, Arial, Helvetica, sans-serif;
  color: #f5f5f5;
  background: #1f2023;
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
  background:
    radial-gradient(circle at center, #292c32 0%, #1b1d21 60%, #151619 100%);
}

button,
input {
  font: inherit;
}

button {
  touch-action: manipulation;
}

.app {
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 12px;
  align-items: stretch;
}

.player {
  width: min(100%, 800px);
}

.main-screen {
  display: grid;
  grid-template-columns: 175px minmax(0, 1fr) 175px;
  gap: 16px;
  margin-top: 10px;
}

.source-column {
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 14px;
}

.now-playing {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.error {
  margin: 10px 0 0;
  padding: 12px;
  border-radius: 12px;
  background: #5a2323;
  color: #ffdede;
  text-align: center;
}

@media (max-width: 700px) {
  .main-screen {
    grid-template-columns: 145px minmax(0, 1fr) 145px;
    gap: 10px;
  }

  .album-cover {
    width: min(100%, 240px);
  }
}

@media (max-height: 520px) {
  .app {
    align-items: flex-start;
    padding: 6px;
  }

  .main-screen {
    grid-template-columns: 155px minmax(0, 1fr) 155px;
    gap: 10px;
    margin-top: 7px;
  }

  .source-column {
    gap: 9px;
  }

  .album-cover {
    width: 205px;
    border-radius: 17px;
  }

  .album-cover__placeholder span {
    font-size: 54px;
  }

  .album-cover__placeholder small {
    font-size: 14px;
  }

  .track-info {
    margin-top: 7px;
  }

  .track-info h1 {
    font-size: 21px;
  }

  .track-info__artist {
    font-size: 16px;
  }

  .track-info__album {
    font-size: 14px;
  }

}
</style>