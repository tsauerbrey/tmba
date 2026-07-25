<script setup>
import { computed } from 'vue'

import AlbumCover from './AlbumCover.vue'
import SourceButton from './SourceButton.vue'

const props = defineProps({
  source: {
    type: String,
    default: 'none',
  },

  coverUrl: {
    type: String,
    default: '',
  },

  title: {
    type: String,
    default: 'Keine Wiedergabe',
  },
})

const emit = defineEmits([
  'select-source',
  'activate-cover',
])

const coverAction = computed(() => {
  switch (props.source) {
    case 'webradio':
      return {
        interactive: true,
        label: 'Sender',
        icon: '☰',
      }

    case 'airplay':
      return {
        interactive: true,
        label: 'Details',
        icon: 'ℹ',
      }

    case 'bluetooth':
      return {
        interactive: true,
        label: 'Geräte',
        icon: '∞',
      }

    case 'usb':
      return {
        interactive: true,
        label: 'Bibliothek',
        icon: '▣',
      }

    default:
      return {
        interactive: false,
        label: '',
        icon: '',
      }
  }
})

function selectSource(sourceName) {
  emit('select-source', sourceName)
}

function activateCover() {
  if (!coverAction.value.interactive) {
    return
  }

  emit('activate-cover', props.source)
}
</script>

<template>
  <section class="main-screen">
    <div class="source-column">
      <SourceButton
        label="AirPlay"
        icon=""
        accent="#168cff"
        :active="source === 'airplay'"
        @select="selectSource('airplay')"
      />

      <SourceButton
        label="Webradio"
        icon="◎"
        accent="#80c43b"
        :active="source === 'webradio'"
        @select="selectSource('webradio')"
      />
    </div>

    <section class="now-playing">
      <AlbumCover
        :cover-url="coverUrl"
        :title="title"
        :interactive="coverAction.interactive"
        :action-label="coverAction.label"
        :action-icon="coverAction.icon"
        @activate="activateCover"
      />
    </section>

    <div class="source-column">
      <SourceButton
        label="Bluetooth"
        icon="∞"
        accent="#168cff"
        :active="source === 'bluetooth'"
        @select="selectSource('bluetooth')"
      />

      <SourceButton
        label="USB/NAS"
        icon="▣"
        accent="#ffc21a"
        :active="source === 'usb'"
        @select="selectSource('usb')"
      />
    </div>
  </section>
</template>

<style scoped>
.main-screen {
  display: grid;
  grid-template-columns: 145px minmax(0, 1fr) 145px;
  align-items: center;
  gap: 18px;
  margin-top: 12px;
}

.source-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.now-playing {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
}

@media (max-width: 700px) {
  .main-screen {
    grid-template-columns: 125px minmax(0, 1fr) 125px;
    gap: 10px;
  }

  .source-column {
    gap: 10px;
  }
}

@media (max-height: 520px) {
  .main-screen {
    grid-template-columns: 125px minmax(0, 1fr) 125px;
    gap: 10px;
    margin-top: 7px;
  }

  .source-column {
    gap: 8px;
  }
}
</style>