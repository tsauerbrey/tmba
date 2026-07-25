<script setup>
import { computed } from 'vue'

const props = defineProps({
  source: {
    type: String,
    default: 'none',
  },

  title: {
    type: String,
    default: 'Keine Wiedergabe',
  },

  artist: {
    type: String,
    default: '',
  },

  album: {
    type: String,
    default: '',
  },

  coverUrl: {
    type: String,
    default: '',
  },

  bluetoothConnected: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
])

const sourceInfo = computed(() => {
  switch (props.source) {
    case 'airplay':
      return {
        name: 'AirPlay',
        icon: '',
        heading: 'AirPlay-Wiedergabe',
        accent: '#168cff',
        description:
          'Die Wiedergabe wird von einem Apple-Gerät an TMBA-OS übertragen.',
        status: 'AirPlay ist als aktive Quelle ausgewählt.',
      }

    case 'bluetooth':
      return {
        name: 'Bluetooth',
        icon: '∞',
        heading: 'Bluetooth-Geräte',
        accent: '#168cff',
        description:
          'Hier werden später gekoppelte und verfügbare Bluetooth-Geräte verwaltet.',
        status: props.bluetoothConnected
          ? 'Ein Bluetooth-Gerät ist verbunden.'
          : 'Derzeit ist kein Bluetooth-Gerät verbunden.',
      }

    case 'usb':
      return {
        name: 'USB / NAS',
        icon: '▣',
        heading: 'Musikbibliothek',
        accent: '#ffc21a',
        description:
          'Hier wird später die Musikbibliothek von USB-Datenträgern und Netzwerkfreigaben angezeigt.',
        status: 'Die USB-/NAS-Bibliothek ist noch nicht eingerichtet.',
      }

    default:
      return {
        name: 'TMBA-OS',
        icon: '♫',
        heading: 'Quelleninformationen',
        accent: '#168cff',
        description:
          'Für die aktuelle Quelle sind noch keine weiteren Funktionen verfügbar.',
        status: 'Keine zusätzliche Quelleninformation vorhanden.',
      }
  }
})

const displayTitle = computed(() => {
  return props.title || 'Keine Wiedergabe'
})

function close() {
  emit('close')
}

function closeOnBackground(event) {
  if (event.target === event.currentTarget) {
    close()
  }
}
</script>

<template>
  <div
    class="source-details"
    role="dialog"
    aria-modal="true"
    :aria-label="sourceInfo.heading"
    @click="closeOnBackground"
  >
    <section
      class="source-details__panel"
      :style="{
        '--source-accent': sourceInfo.accent,
      }"
    >
      <header class="source-details__header">
        <div class="source-details__source">
          <span class="source-details__source-icon">
            {{ sourceInfo.icon }}
          </span>

          <div class="source-details__heading">
            <small>{{ sourceInfo.name }}</small>
            <h2>{{ sourceInfo.heading }}</h2>
          </div>
        </div>

        <button
          class="source-details__close"
          type="button"
          aria-label="Ansicht schließen"
          @click="close"
        >
          ×
        </button>
      </header>

      <div class="source-details__content">
        <div class="source-details__cover">
          <img
            v-if="coverUrl"
            :src="coverUrl"
            :alt="`Cover: ${displayTitle}`"
          />

          <div
            v-else
            class="source-details__placeholder"
          >
            <span>♫</span>
            <small>TMBA-OS</small>
          </div>
        </div>

        <div class="source-details__information">
          <p class="source-details__description">
            {{ sourceInfo.description }}
          </p>

          <p class="source-details__status">
            <span class="source-details__status-dot"></span>
            {{ sourceInfo.status }}
          </p>

          <dl class="source-details__metadata">
            <div>
              <dt>Titel</dt>
              <dd>{{ displayTitle }}</dd>
            </div>

            <div v-if="artist">
              <dt>Interpret</dt>
              <dd>{{ artist }}</dd>
            </div>

            <div v-if="album">
              <dt>Album</dt>
              <dd>{{ album }}</dd>
            </div>

            <div>
              <dt>Quelle</dt>
              <dd>{{ sourceInfo.name }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.source-details {
  position: fixed;
  z-index: 100;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  background: rgb(0 0 0 / 74%);
  backdrop-filter: blur(10px);
}

.source-details__panel {
  width: min(720px, 100%);
  max-height: calc(100vh - 28px);
  overflow: auto;
  border: 1px solid #343b46;
  border-radius: 24px;
  background:
    linear-gradient(
      145deg,
      rgb(24 29 37 / 98%),
      rgb(10 13 18 / 98%)
    );
  box-shadow:
    0 24px 70px rgb(0 0 0 / 58%),
    0 0 32px color-mix(
      in srgb,
      var(--source-accent) 12%,
      transparent
    );
}

.source-details__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 17px 20px;
  border-bottom: 1px solid rgb(255 255 255 / 8%);
}

.source-details__source {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 14px;
}

.source-details__source-icon {
  display: flex;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 1px solid
    color-mix(
      in srgb,
      var(--source-accent) 45%,
      transparent
    );
  border-radius: 15px;
  background:
    color-mix(
      in srgb,
      var(--source-accent) 14%,
      transparent
    );
  color: var(--source-accent);
  font-size: 25px;
  font-weight: 800;
}

.source-details__heading {
  min-width: 0;
}

.source-details__heading small {
  color: #8e9baa;
  font-size: 12px;
  font-weight: 750;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.source-details__heading h2 {
  overflow: hidden;
  margin: 3px 0 0;
  color: #f1f5f9;
  font-size: 22px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-details__close {
  display: flex;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 14px;
  background: rgb(255 255 255 / 6%);
  color: #dfe8f1;
  cursor: pointer;
  font-size: 30px;
  line-height: 1;
}

.source-details__close:active {
  transform: scale(0.94);
}

.source-details__content {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  padding: 22px;
}

.source-details__cover {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid #3a3e47;
  border-radius: 18px;
  background:
    radial-gradient(
      circle at 50% 35%,
      #174b78 0%,
      #0e2439 35%,
      #090d13 100%
    );
  box-shadow: 0 12px 28px rgb(0 0 0 / 32%);
}

.source-details__cover img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.source-details__placeholder {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--source-accent);
}

.source-details__placeholder span {
  font-size: 58px;
}

.source-details__placeholder small {
  margin-top: 8px;
  color: #dfe8f1;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.source-details__information {
  min-width: 0;
}

.source-details__description {
  margin: 0 0 14px;
  color: #aeb8c4;
  font-size: 15px;
  line-height: 1.45;
}

.source-details__status {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 16px;
  padding: 10px 12px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 12px;
  background: rgb(255 255 255 / 4%);
  color: #dbe4ed;
  font-size: 13px;
  font-weight: 650;
}

.source-details__status-dot {
  width: 9px;
  height: 9px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--source-accent);
  box-shadow:
    0 0 10px
    color-mix(
      in srgb,
      var(--source-accent) 60%,
      transparent
    );
}

.source-details__metadata {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin: 0;
}

.source-details__metadata div {
  padding: 10px 12px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 12px;
  background: rgb(255 255 255 / 4%);
}

.source-details__metadata dt {
  margin-bottom: 4px;
  color: #778493;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.source-details__metadata dd {
  overflow: hidden;
  margin: 0;
  color: #edf3f8;
  font-size: 15px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-height: 520px) {
  .source-details {
    padding: 8px;
  }

  .source-details__panel {
    max-height: calc(100vh - 16px);
    border-radius: 18px;
  }

  .source-details__header {
    padding: 9px 14px;
  }

  .source-details__source-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    font-size: 20px;
  }

  .source-details__heading h2 {
    font-size: 18px;
  }

  .source-details__close {
    width: 38px;
    height: 38px;
  }

  .source-details__content {
    grid-template-columns: 165px minmax(0, 1fr);
    gap: 16px;
    padding: 13px;
  }

  .source-details__description {
    margin-bottom: 8px;
    font-size: 13px;
  }

  .source-details__status {
    margin-bottom: 8px;
    padding: 7px 9px;
    font-size: 12px;
  }

  .source-details__metadata {
    gap: 5px;
  }

  .source-details__metadata div {
    padding: 6px 9px;
  }

  .source-details__metadata dt {
    margin-bottom: 2px;
    font-size: 9px;
  }

  .source-details__metadata dd {
    font-size: 12px;
  }
}
</style>