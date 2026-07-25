<script setup>
import { computed, ref, watch } from 'vue'

import WifiKeyboard from './WifiKeyboard.vue'
import WifiSignal from './WifiSignal.vue'

const props = defineProps({
  network: {
    type: Object,
    required: true,
  },

  pending: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
  'connect',
])

const password = ref('')
const showPassword = ref(false)
const keyboardOpen = ref(true)

const secureNetwork = computed(() => {
  const security = String(props.network.security ?? '').toLowerCase()

  return Boolean(
    security
    && security !== 'offen'
    && security !== '--'
    && security !== 'none',
  )
})

watch(
  () => props.network.ssid,
  () => {
    password.value = ''
    keyboardOpen.value = true
  },
)

function submit() {
  emit('connect', {
    ssid: props.network.ssid,
    password: secureNetwork.value ? password.value : '',
    hidden: false,
  })
}
</script>

<template>
  <div
    class="dialog-backdrop"
    @click.self="$emit('close')"
  >
    <section
      class="wifi-dialog"
      role="dialog"
      aria-modal="true"
      :aria-label="`Mit ${network.ssid} verbinden`"
    >
      <header class="dialog-header">
        <div class="network-title">
          <WifiSignal :signal="network.signal_percent" />

          <div>
            <strong>{{ network.ssid }}</strong>
            <small>{{ network.security || 'Offenes Netzwerk' }}</small>
          </div>
        </div>

        <button
          type="button"
          class="close-button"
          aria-label="Dialog schließen"
          @click="$emit('close')"
        >
          ×
        </button>
      </header>

      <div
        v-if="secureNetwork"
        class="password-row"
      >
        <input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="WLAN-Passwort"
          autofocus
          @focus="keyboardOpen = true"
          @keyup.enter="submit"
        >

        <button
          type="button"
          class="secondary-button"
          @click="showPassword = !showPassword"
        >
          {{ showPassword ? 'Verbergen' : 'Anzeigen' }}
        </button>
      </div>

      <p
        v-else
        class="open-network"
      >
        Dieses Netzwerk benötigt kein Passwort.
      </p>

      <WifiKeyboard
        v-if="keyboardOpen && secureNetwork"
        v-model="password"
        @close="keyboardOpen = false"
        @submit="submit"
      />

      <footer
        v-else
        class="dialog-actions"
      >
        <button
          type="button"
          class="secondary-button"
          @click="$emit('close')"
        >
          Abbrechen
        </button>

        <button
          type="button"
          class="connect-button"
          :disabled="pending"
          @click="submit"
        >
          {{ pending ? 'Verbindet …' : 'Verbinden' }}
        </button>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.dialog-backdrop {
  position: fixed;
  z-index: 30;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: rgb(0 0 0 / 76%);
}

.wifi-dialog {
  width: min(780px, 100%);
  max-height: calc(100vh - 16px);
  overflow-y: auto;
  padding: 14px;
  border: 1px solid rgb(255 255 255 / 14%);
  border-radius: 18px;
  background: #202329;
  box-shadow: 0 20px 60px rgb(0 0 0 / 45%);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.network-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.network-title strong,
.network-title small {
  display: block;
}

.network-title strong {
  overflow: hidden;
  font-size: 21px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.network-title small {
  margin-top: 2px;
  color: #aeb5c0;
}

.close-button {
  width: 44px;
  height: 44px;
  border: 0;
  border-radius: 50%;
  background: #353941;
  color: #fff;
  font-size: 28px;
  cursor: pointer;
}

.password-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  margin-top: 12px;
}

.password-row input {
  min-width: 0;
  height: 48px;
  padding: 0 14px;
  border: 1px solid rgb(255 255 255 / 17%);
  border-radius: 10px;
  outline: none;
  background: #15171b;
  color: #fff;
  font-size: 18px;
}

.password-row input:focus {
  border-color: #80c43b;
}

.open-network {
  margin: 20px 0;
  color: #cfd4dc;
  text-align: center;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.secondary-button,
.connect-button {
  min-height: 44px;
  padding: 0 18px;
  border: 0;
  border-radius: 10px;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button {
  background: #3a3e47;
}

.connect-button {
  background: #4b8f20;
}

@media (max-height: 520px) {
  .wifi-dialog {
    padding: 10px;
  }

  .network-title strong {
    font-size: 18px;
  }

  .password-row {
    margin-top: 8px;
  }
}
</style>
