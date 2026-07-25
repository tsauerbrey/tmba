<script setup>
import { computed } from 'vue'

const props = defineProps({
  signal: {
    type: Number,
    default: null,
  },
})

const normalizedSignal = computed(() => {
  if (props.signal === null || Number.isNaN(props.signal)) {
    return 0
  }

  return Math.max(0, Math.min(100, props.signal))
})

const activeBars = computed(() => {
  if (normalizedSignal.value >= 75) return 4
  if (normalizedSignal.value >= 50) return 3
  if (normalizedSignal.value >= 25) return 2
  if (normalizedSignal.value > 0) return 1
  return 0
})
</script>

<template>
  <span
    class="wifi-signal"
    :title="`${normalizedSignal}%`"
    :aria-label="`WLAN-Signal ${normalizedSignal} Prozent`"
  >
    <span
      v-for="bar in 4"
      :key="bar"
      class="signal-bar"
      :class="{ active: bar <= activeBars }"
    />
  </span>
</template>

<style scoped>
.wifi-signal {
  display: inline-flex;
  height: 24px;
  align-items: flex-end;
  gap: 3px;
}

.signal-bar {
  width: 5px;
  border-radius: 3px 3px 1px 1px;
  background: rgb(255 255 255 / 20%);
}

.signal-bar:nth-child(1) {
  height: 7px;
}

.signal-bar:nth-child(2) {
  height: 12px;
}

.signal-bar:nth-child(3) {
  height: 18px;
}

.signal-bar:nth-child(4) {
  height: 24px;
}

.signal-bar.active {
  background: #80c43b;
}
</style>
