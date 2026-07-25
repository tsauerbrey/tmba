<script setup>
defineProps({
  label: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
  accent: {
    type: String,
    default: '#168cff',
  },
})

defineEmits(['select'])
</script>

<template>
  <button
    class="source-button"
    :class="{ 'source-button--active': active }"
    :style="{ '--source-accent': accent }"
    type="button"
    :aria-pressed="active"
    @click="$emit('select')"
  >
    <span class="source-button__icon">
      {{ icon }}
    </span>

    <span class="source-button__label">
      {{ label }}
    </span>
  </button>
</template>

<style scoped>
.source-button {
  display: flex;
  min-width: 0;
  min-height: 132px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid #343841;
  border-radius: 22px;
  background:
    linear-gradient(
      145deg,
      rgb(31 34 40 / 96%),
      rgb(15 17 21 / 96%)
    );
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 4%),
    0 12px 28px rgb(0 0 0 / 25%);
  color: var(--source-accent);
  cursor: pointer;
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    transform 120ms ease;
}

.source-button:hover {
  border-color: color-mix(in srgb, var(--source-accent) 65%, #343841);
}

.source-button:active {
  transform: scale(0.97);
}

.source-button--active {
  border-color: var(--source-accent);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 6%),
    0 0 20px color-mix(in srgb, var(--source-accent) 35%, transparent);
}

.source-button__icon {
  font-size: 44px;
  line-height: 1;
}

.source-button__label {
  overflow: hidden;
  max-width: 100%;
  font-size: 20px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-height: 520px) {
  .source-button {
    min-height: 118px;
    gap: 9px;
    border-radius: 18px;
  }

  .source-button__icon {
    font-size: 38px;
  }

  .source-button__label {
    font-size: 18px;
  }
}
</style>