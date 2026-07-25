<script setup>
defineProps({
  volume: {
    type: Number,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['change'])
</script>

<template>
  <section class="volume-bar">
    <div class="volume-bar__center">
      <strong class="volume-bar__value">
        {{ volume }} %
      </strong>

      <input
        class="volume-bar__slider"
        type="range"
        min="0"
        max="100"
        step="1"
        :value="volume"
        :disabled="disabled"
        aria-label="Lautstärke"
        @input="$emit('change', Number($event.target.value))"
      />
    </div>
  </section>
</template>

<style scoped>
.volume-bar {
  height: 100%;
  box-sizing: border-box;
  padding: 10px 20px;
  border: 1px solid #343841;
  border-radius: 16px;
  background: linear-gradient(
    145deg,
    rgb(31 34 40 / 96%),
    rgb(15 17 21 / 96%)
  );
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 4%),
    0 8px 20px rgb(0 0 0 / 18%);
}

.volume-bar__center {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.volume-bar__value {
  text-align: center;
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
}

.volume-bar__slider {
  width: 100%;
  height: 5px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
}

.volume-bar__slider::-webkit-slider-runnable-track {
  height: 5px;
  border-radius: 999px;
  background: #343941;
}

.volume-bar__slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  margin-top: -5.5px;
  border-radius: 50%;
  background: #168cff;
  border: 2px solid #dcecff;
  box-shadow: 0 2px 8px rgb(0 0 0 / 35%);
}

.volume-bar__slider::-moz-range-track {
  height: 5px;
  border: none;
  border-radius: 999px;
  background: #343941;
}

.volume-bar__slider::-moz-range-progress {
  height: 5px;
  border-radius: 999px;
  background: #168cff;
}

.volume-bar__slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #168cff;
  border: 2px solid #dcecff;
}

@media (max-height: 520px) {
  .volume-bar {
    padding: 8px 16px;
  }

  .volume-bar__value {
    font-size: 14px;
  }

  .volume-bar__slider {
    height: 4px;
  }

  .volume-bar__slider::-webkit-slider-runnable-track,
  .volume-bar__slider::-moz-range-track,
  .volume-bar__slider::-moz-range-progress {
    height: 4px;
  }

  .volume-bar__slider::-webkit-slider-thumb,
  .volume-bar__slider::-moz-range-thumb {
    width: 14px;
    height: 14px;
    margin-top: -5px;
  }
}
</style>