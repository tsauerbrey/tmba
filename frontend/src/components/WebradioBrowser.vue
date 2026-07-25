<script setup>
import {
  computed,
  ref,
} from 'vue'
import { storeToRefs } from 'pinia'

import LocalStations from './LocalStations.vue'
import OnlineSearch from './OnlineSearch.vue'

import { useWebradioStore } from '../stores/webradio'

const emit = defineEmits([
  'close',
])

const webradioStore = useWebradioStore()

const {
  stations,
  onlineStations,
} = storeToRefs(webradioStore)

const activeTab = ref('local')

const localCount = computed(
  () => stations.value.length,
)

const onlineCount = computed(
  () => onlineStations.value.length,
)

function close() {
  emit('close')
}
</script>

<template>
  <div
    class="browser-backdrop"
    @click.self="close"
  >
    <section
      class="browser"
      role="dialog"
      aria-modal="true"
      aria-label="Webradio"
    >
      <header class="browser__header">
        <div class="browser__heading">
          <p class="browser__eyebrow">
            TMBA-OS
          </p>

          <h2>Webradio</h2>
        </div>

        <button
          class="browser__close"
          type="button"
          aria-label="Webradio schließen"
          @click="close"
        >
          ×
        </button>
      </header>

      <nav
        class="browser__tabs"
        aria-label="Webradio-Bereiche"
      >
        <button
          class="browser__tab"
          :class="{
            'browser__tab--active':
              activeTab === 'local',
          }"
          type="button"
          @click="activeTab = 'local'"
        >
          <span aria-hidden="true">★</span>
          Meine Sender

          <b>{{ localCount }}</b>
        </button>

        <button
          class="browser__tab"
          :class="{
            'browser__tab--active':
              activeTab === 'online',
          }"
          type="button"
          @click="activeTab = 'online'"
        >
          <span aria-hidden="true">⌕</span>
          Online suchen

          <b v-if="onlineCount">
            {{ onlineCount }}
          </b>
        </button>
      </nav>

      <div class="browser__content">
        <LocalStations
          v-if="activeTab === 'local'"
        />

        <OnlineSearch v-else />
      </div>

      <footer class="browser__footer">
        <span v-if="activeTab === 'local'">
          Gespeicherte Sender und Favoriten
        </span>

        <span v-else>
          Sender suchen, testen und speichern
        </span>

        <button
          class="browser__done"
          type="button"
          @click="close"
        >
          Fertig
        </button>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.browser-backdrop {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px;
  background: rgb(5 7 10 / 84%);
  backdrop-filter: blur(9px);
}

.browser {
  display: flex;
  width: min(720px, 100%);
  max-height: min(
    452px,
    calc(100vh - 20px)
  );
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 24px;
  background:
    linear-gradient(
      145deg,
      rgb(42 45 51 / 98%),
      rgb(24 26 30 / 98%)
    );
  box-shadow:
    0 28px 80px rgb(0 0 0 / 58%),
    0 0 32px rgb(128 196 59 / 7%);
}

.browser__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.browser__eyebrow {
  margin: 0 0 2px;
  color: #80c43b;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.browser__header h2 {
  margin: 0;
  color: #f5f7f9;
  font-size: 25px;
}

.browser__close {
  display: flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgb(255 255 255 / 8%);
  border-radius: 13px;
  background: rgb(255 255 255 / 7%);
  color: #fff;
  cursor: pointer;
  font-size: 29px;
  line-height: 1;
}

.browser__tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 10px 0;
  padding: 4px;
  border-radius: 14px;
  background: rgb(0 0 0 / 23%);
}

.browser__tab {
  display: flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: transparent;
  color: #9fa6af;
  cursor: pointer;
  font-size: 13px;
  font-weight: 800;
}

.browser__tab span {
  font-size: 18px;
}

.browser__tab b {
  display: flex;
  min-width: 21px;
  height: 21px;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  border-radius: 7px;
  background: rgb(0 0 0 / 25%);
  font-size: 10px;
}

.browser__tab--active {
  border-color: rgb(128 196 59 / 45%);
  background: rgb(128 196 59 / 15%);
  color: #e8ffd4;
}

.browser__content {
  display: flex;
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.browser__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 9px;
  padding-top: 9px;
  border-top: 1px solid rgb(255 255 255 / 7%);
}

.browser__footer span {
  color: #858c95;
  font-size: 11px;
}

.browser__done {
  min-width: 88px;
  min-height: 37px;
  padding: 7px 16px;
  border: 1px solid rgb(128 196 59 / 55%);
  border-radius: 11px;
  background: rgb(128 196 59 / 16%);
  color: #e7ffd1;
  cursor: pointer;
  font-size: 13px;
  font-weight: 800;
}

@media (max-height: 520px) {
  .browser-backdrop {
    padding: 6px;
  }

  .browser {
    max-height: calc(100vh - 12px);
    padding: 10px 12px;
    border-radius: 18px;
  }

  .browser__header h2 {
    font-size: 20px;
  }

  .browser__close {
    width: 37px;
    height: 37px;
  }

  .browser__tabs {
    margin: 6px 0;
  }

  .browser__tab {
    min-height: 34px;
    font-size: 12px;
  }

  .browser__footer {
    margin-top: 6px;
    padding-top: 6px;
  }

  .browser__done {
    min-height: 33px;
  }
}
</style>