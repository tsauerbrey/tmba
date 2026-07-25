<script setup>
defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },

  isPlaying: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'play',
  'pause',
  'stop',
  'previous',
  'next',
])
</script>

<template>
  <section class="player-controls">
    <button
      class="control-button"
      type="button"
      aria-label="Vorheriger Titel"
      title="Vorheriger Titel"
      :disabled="disabled"
      @click="emit('previous')"
    >
      ⏮
    </button>

    <button
      class="control-button"
      type="button"
      aria-label="Wiedergabe stoppen"
      title="Stopp"
      :disabled="disabled"
      @click="emit('stop')"
    >
      ■
    </button>

    <button
      v-if="isPlaying"
      class="control-button control-button--primary"
      type="button"
      aria-label="Wiedergabe pausieren"
      title="Pause"
      :disabled="disabled"
      @click="emit('pause')"
    >
      ⏸
    </button>

    <button
      v-else
      class="control-button control-button--primary"
      type="button"
      aria-label="Wiedergabe starten"
      title="Wiedergabe"
      :disabled="disabled"
      @click="emit('play')"
    >
      ▶
    </button>

    <button
      class="control-button"
      type="button"
      aria-label="Nächster Titel"
      title="Nächster Titel"
      :disabled="disabled"
      @click="emit('next')"
    >
      ⏭
    </button>
  </section>
</template>

<style scoped>
.player-controls {
  display: grid;
  min-height: 92px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: center;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgb(255 255 255 / 5%);
  border-radius: 20px;
  background: linear-gradient(145deg, #292c31, #202226);
  box-shadow:
    8px 8px 18px rgb(0 0 0 / 35%),
    -5px -5px 14px rgb(255 255 255 / 3%);
}

.control-button {
  display: flex;
  min-width: 0;
  height: 58px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 15px;
  background: linear-gradient(145deg, #2d3035, #222429);
  box-shadow:
    5px 5px 10px rgb(0 0 0 / 40%),
    -3px -3px 8px rgb(255 255 255 / 4%);
  color: #e9e9e9;
  cursor: pointer;
  font-size: 25px;
  line-height: 1;
  transition:
    transform 100ms ease,
    box-shadow 100ms ease,
    color 100ms ease;
}

.control-button:hover:not(:disabled) {
  color: #ffffff;
}

.control-button:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow:
    inset 4px 4px 8px rgb(0 0 0 / 35%),
    inset -3px -3px 7px rgb(255 255 255 / 3%);
}

.control-button--primary {
  color: #76d7ff;
  box-shadow:
    0 0 15px rgb(71 190 238 / 15%),
    5px 5px 10px rgb(0 0 0 / 40%),
    -3px -3px 8px rgb(255 255 255 / 4%);
}

@media (max-height: 520px) {
  .player-controls {
    min-height: 76px;
    gap: 7px;
    padding: 10px;
    border-radius: 16px;
  }

  .control-button {
    height: 50px;
    border-radius: 12px;
    font-size: 22px;
  }
}
</style>