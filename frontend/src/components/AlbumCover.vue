<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  coverUrl: {
    type: String,
    default: '',
  },

  title: {
    type: String,
    default: 'TMBA-OS',
  },

  interactive: {
    type: Boolean,
    default: false,
  },

  actionLabel: {
    type: String,
    default: 'Details',
  },

  actionIcon: {
    type: String,
    default: '☰',
  },
})

const emit = defineEmits([
  'activate',
])

const imageLoaded = ref(false)
const imageFailed = ref(false)

watch(
  () => props.coverUrl,
  () => {
    imageLoaded.value = false
    imageFailed.value = false
  },
)

function handleImageLoad() {
  imageLoaded.value = true
  imageFailed.value = false
}

function handleImageError() {
  imageLoaded.value = false
  imageFailed.value = true
}

function activate() {
  if (!props.interactive) {
    return
  }

  emit('activate')
}
</script>

<template>
  <div
    class="album-cover"
    :class="{
      'album-cover--interactive': interactive,
    }"
    :role="interactive ? 'button' : undefined"
    :tabindex="interactive ? 0 : undefined"
    :aria-label="
      interactive
        ? `${actionLabel} öffnen`
        : undefined
    "
    @click="activate"
    @keydown.enter="activate"
    @keydown.space.prevent="activate"
  >
    <div
      v-if="!coverUrl || imageFailed"
      class="album-cover__placeholder"
    >
      <span>♫</span>
      <small>TMBA-OS</small>
    </div>

    <div
      v-else-if="!imageLoaded"
      class="album-cover__loading"
      aria-label="Cover wird geladen"
    >
      <span class="album-cover__spinner"></span>
      <small>Cover wird geladen</small>
    </div>

    <img
      v-if="coverUrl && !imageFailed"
      :key="coverUrl"
      class="album-cover__image"
      :class="{
        'album-cover__image--visible': imageLoaded,
      }"
      :src="coverUrl"
      :alt="`Albumcover: ${title}`"
      @load="handleImageLoad"
      @error="handleImageError"
    />

    <div
      v-if="interactive"
      class="album-cover__action"
      aria-hidden="true"
    >
      <span class="album-cover__action-icon">
        {{ actionIcon }}
      </span>

      <span class="album-cover__action-label">
        {{ actionLabel }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.album-cover {
  position: relative;
  width: min(100%, 280px);
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid #3a3e47;
  border-radius: 22px;
  background:
    radial-gradient(
      circle at 50% 35%,
      #174b78 0%,
      #0e2439 35%,
      #090d13 100%
    );
  box-shadow:
    0 15px 35px rgb(0 0 0 / 35%),
    0 0 22px rgb(22 140 255 / 10%);
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.album-cover--interactive {
  cursor: pointer;
  touch-action: manipulation;
}

.album-cover--interactive:hover {
  border-color: rgb(128 196 59 / 62%);
  box-shadow:
    0 15px 35px rgb(0 0 0 / 35%),
    0 0 25px rgb(128 196 59 / 16%);
}

.album-cover--interactive:focus-visible {
  outline: 3px solid rgb(128 196 59 / 75%);
  outline-offset: 4px;
}

.album-cover__image {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transform: scale(1.025);
  transition:
    opacity 320ms ease,
    transform 450ms ease;
}

.album-cover__image--visible {
  opacity: 1;
  transform: scale(1);
}

.album-cover__placeholder,
.album-cover__loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.album-cover__placeholder {
  color: #168cff;
}

.album-cover__placeholder span {
  font-size: 72px;
}

.album-cover__placeholder small {
  margin-top: 12px;
  color: #dfe8f1;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.album-cover__loading {
  gap: 14px;
  color: #aeb8c4;
}

.album-cover__loading small {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.album-cover__spinner {
  width: 42px;
  height: 42px;
  border: 4px solid rgb(255 255 255 / 14%);
  border-top-color: #168cff;
  border-radius: 50%;
  animation: album-cover-spin 850ms linear infinite;
}

.album-cover__action {
  position: absolute;
  z-index: 3;
  right: 10px;
  bottom: 10px;
  display: flex;
  min-height: 34px;
  align-items: center;
  gap: 7px;
  padding: 6px 11px;
  border: 1px solid rgb(255 255 255 / 18%);
  border-radius: 12px;
  background: rgb(10 12 14 / 78%);
  color: #f3ffe8;
  font-size: 13px;
  font-weight: 750;
  box-shadow:
    0 5px 18px rgb(0 0 0 / 36%),
    0 0 14px rgb(128 196 59 / 12%);
  backdrop-filter: blur(7px);
  pointer-events: none;
}

.album-cover__action-icon {
  color: #80c43b;
  font-size: 17px;
  line-height: 1;
}

.album-cover__action-label {
  line-height: 1;
}

@keyframes album-cover-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .album-cover,
  .album-cover__image {
    transition: none;
  }

  .album-cover__spinner {
    animation: none;
  }
}

@media (max-width: 700px) {
  .album-cover {
    width: min(100%, 240px);
  }
}

@media (max-height: 520px) {
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

  .album-cover__spinner {
    width: 34px;
    height: 34px;
  }

  .album-cover__action {
    right: 7px;
    bottom: 7px;
    min-height: 30px;
    padding: 5px 9px;
    border-radius: 10px;
    font-size: 12px;
  }

  .album-cover__action-icon {
    font-size: 15px;
  }
}
</style>