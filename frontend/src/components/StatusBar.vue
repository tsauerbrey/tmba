<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

defineProps({
  volume: {
    type: Number,
    default: 0,
  },
  wifiConnected: {
    type: Boolean,
    default: true,
  },
  bluetoothConnected: {
    type: Boolean,
    default: false,
  },
})

const currentTime = ref('')
const currentDate = ref('')

let clockTimer

function updateClock() {
  const now = new Date()

  currentTime.value = now.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
  })

  currentDate.value = now.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function openMenu() {
  console.log('Menü öffnen')
}

function openSettings() {
  console.log('Einstellungen öffnen')
}

onMounted(() => {
  updateClock()
  clockTimer = window.setInterval(updateClock, 1000)
})

onBeforeUnmount(() => {
  window.clearInterval(clockTimer)
})
</script>

<template>
  <header class="status-bar">
    <div class="status-bar__left">
      <button
        class="icon-button"
        type="button"
        aria-label="Menü öffnen"
        @click="openMenu"
      >
        ☰
      </button>

      <div class="brand">
        <span class="brand__icon">♫</span>
        <span class="brand__name">TMBA-OS</span>
      </div>
    </div>

    <div class="clock">
      <strong>{{ currentTime }}</strong>
      <span>{{ currentDate }}</span>
    </div>

    <div class="status-bar__right">
      <div class="status-item" aria-label="Lautstärke">
        <span class="status-item__icon">🔊</span>
        <span>{{ volume }} %</span>
      </div>

      <div
        class="connection-icon"
        :class="{ 'connection-icon--inactive': !wifiConnected }"
        :title="wifiConnected ? 'WLAN verbunden' : 'WLAN nicht verbunden'"
      >
        ◉
      </div>

      <div
        class="connection-icon connection-icon--bluetooth"
        :class="{ 'connection-icon--inactive': !bluetoothConnected }"
        :title="
          bluetoothConnected
            ? 'Bluetooth verbunden'
            : 'Bluetooth nicht verbunden'
        "
      >
        ᛒ
      </div>

      <button
        class="icon-button"
        type="button"
        aria-label="Einstellungen öffnen"
        @click="openSettings"
      >
        ⚙
      </button>
    </div>
  </header>
</template>

<style scoped>
.status-bar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 82px;
  padding: 10px 14px;
  border: 1px solid #30333a;
  border-radius: 20px;
  background: linear-gradient(180deg, #111317 0%, #090a0c 100%);
  box-shadow: 0 12px 35px rgb(0 0 0 / 28%);
}

.status-bar__left,
.status-bar__right {
  display: flex;
  align-items: center;
  gap: 18px;
}

.status-bar__right {
  justify-content: flex-end;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand__icon {
  color: #168cff;
  font-size: 38px;
  line-height: 1;
}

.brand__name {
  color: #f7f7f8;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.clock {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
}

.clock strong {
  color: #ffffff;
  font-size: 28px;
}

.clock span {
  margin-top: 5px;
  color: #8f949e;
  font-size: 15px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #f4f4f5;
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
}

.status-item__icon {
  font-size: 21px;
}

.connection-icon {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  color: #168cff;
  font-size: 27px;
  font-weight: 800;
}

.connection-icon--bluetooth {
  font-size: 31px;
}

.connection-icon--inactive {
  color: #555a64;
  opacity: 0.65;
}

.icon-button {
  display: grid;
  width: 54px;
  height: 54px;
  padding: 0;
  place-items: center;
  border: 1px solid #30333a;
  border-radius: 15px;
  background: #17191e;
  color: #f7f7f8;
  cursor: pointer;
  font-size: 29px;
}

.icon-button:active {
  transform: scale(0.96);
  background: #22252c;
}

@media (max-width: 700px) {
  .status-bar {
    min-height: 72px;
    padding: 8px 10px;
  }

  .status-bar__left,
  .status-bar__right {
    gap: 10px;
  }

  .brand__name {
    font-size: 23px;
  }

  .brand__icon {
    font-size: 31px;
  }

  .clock strong {
    font-size: 23px;
  }

  .clock span {
    font-size: 13px;
  }

  .status-item {
    font-size: 16px;
  }

  .icon-button {
    width: 46px;
    height: 46px;
    font-size: 24px;
  }

  .connection-icon {
    width: 31px;
    height: 31px;
    font-size: 23px;
  }
}
</style>