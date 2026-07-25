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
  position: relative;
  isolation: isolate;
  display: flex;
  min-width: 0;
  min-height: 132px;
  overflow: hidden;
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
    border-color 180ms ease,
    box-shadow 220ms ease,
    transform 120ms ease,
    background 220ms ease;
}

.source-button::before {
  position: absolute;
  z-index: -1;
  inset: -35%;
  border-radius: 50%;
  background:
    radial-gradient(
      circle,
      color-mix(in srgb, var(--source-accent) 26%, transparent) 0%,
      transparent 65%
    );
  content: '';
  opacity: 0;
  transform: scale(0.72);
  transition:
    opacity 220ms ease,
    transform 260ms ease;
}

.source-button::after {
  position: absolute;
  inset: 0;
  border: 1px solid transparent;
  border-radius: inherit;
  content: '';
  pointer-events: none;
}

.source-button:hover {
  border-color:
    color-mix(
      in srgb,
      var(--source-accent) 65%,
      #343841
    );
}

.source-button:hover::before {
  opacity: 0.38;
  transform: scale(0.9);
}

.source-button:active {
  transform: scale(0.97);
}

.source-button--active {
  border-color: var(--source-accent);
  background:
    linear-gradient(
      145deg,
      color-mix(
        in srgb,
        var(--source-accent) 10%,
        rgb(31 34 40 / 96%)
      ),
      rgb(15 17 21 / 96%)
    );
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 7%),
    0 0 20px
      color-mix(
        in srgb,
        var(--source-accent) 34%,
        transparent
      );
  animation:
    source-button-glow 2.6s ease-in-out infinite;
}

.source-button--active::before {
  opacity: 0.62;
  transform: scale(1);
  animation:
    source-button-pulse 2.6s ease-in-out infinite;
}

.source-button--active::after {
  border-color:
    color-mix(
      in srgb,
      var(--source-accent) 72%,
      transparent
    );
  animation:
    source-button-ring 2.6s ease-out infinite;
}

.source-button__icon,
.source-button__label {
  position: relative;
  z-index: 1;
}

.source-button__icon {
  font-size: 44px;
  line-height: 1;
  transition:
    filter 220ms ease,
    transform 220ms ease;
}

.source-button--active .source-button__icon {
  filter:
    drop-shadow(
      0 0 8px
      color-mix(
        in srgb,
        var(--source-accent) 55%,
        transparent
      )
    );
  transform: scale(1.04);
}

.source-button__label {
  overflow: hidden;
  max-width: 100%;
  font-size: 20px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes source-button-glow {
  0%,
  100% {
    box-shadow:
      inset 0 1px 0 rgb(255 255 255 / 7%),
      0 0 16px
        color-mix(
          in srgb,
          var(--source-accent) 24%,
          transparent
        );
  }

  50% {
    box-shadow:
      inset 0 1px 0 rgb(255 255 255 / 7%),
      0 0 28px
        color-mix(
          in srgb,
          var(--source-accent) 44%,
          transparent
        );
  }
}

@keyframes source-button-pulse {
  0%,
  100% {
    opacity: 0.42;
    transform: scale(0.9);
  }

  50% {
    opacity: 0.68;
    transform: scale(1.05);
  }
}

@keyframes source-button-ring {
  0% {
    opacity: 0.65;
    transform: scale(0.96);
  }

  70%,
  100% {
    opacity: 0;
    transform: scale(1.08);
  }
}

@media (prefers-reduced-motion: reduce) {
  .source-button,
  .source-button::before,
  .source-button::after,
  .source-button__icon {
    animation: none;
    transition: none;
  }
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