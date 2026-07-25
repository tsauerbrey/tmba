<script setup>
const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'update:modelValue',
  'close',
  'submit',
])

const rows = [
  ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
  ['q', 'w', 'e', 'r', 't', 'z', 'u', 'i', 'o', 'p'],
  ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
  ['y', 'x', 'c', 'v', 'b', 'n', 'm', '-', '_'],
]

function append(character) {
  emit('update:modelValue', `${props.modelValue}${character}`)
}

function backspace() {
  emit(
    'update:modelValue',
    props.modelValue.slice(0, -1),
  )
}
</script>

<template>
  <section class="keyboard">
    <div
      v-for="(row, rowIndex) in rows"
      :key="rowIndex"
      class="keyboard-row"
    >
      <button
        v-for="key in row"
        :key="key"
        type="button"
        class="key"
        @click="append(key)"
      >
        {{ key }}
      </button>
    </div>

    <div class="keyboard-row action-row">
      <button
        type="button"
        class="key wide"
        @click="append(' ')"
      >
        Leerzeichen
      </button>

      <button
        type="button"
        class="key action"
        @click="backspace"
      >
        ⌫
      </button>

      <button
        type="button"
        class="key action"
        @click="$emit('close')"
      >
        Fertig
      </button>

      <button
        type="button"
        class="key confirm"
        @click="$emit('submit')"
      >
        Verbinden
      </button>
    </div>
  </section>
</template>

<style scoped>
.keyboard {
  display: grid;
  gap: 6px;
  padding-top: 10px;
}

.keyboard-row {
  display: flex;
  justify-content: center;
  gap: 5px;
}

.key {
  min-width: 42px;
  min-height: 42px;
  padding: 4px 8px;
  border: 1px solid rgb(255 255 255 / 14%);
  border-radius: 9px;
  background: #343840;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
}

.key:active {
  transform: scale(0.96);
  background: #48505c;
}

.key.wide {
  min-width: 190px;
}

.key.action {
  min-width: 76px;
}

.key.confirm {
  min-width: 105px;
  background: #397415;
}

@media (max-width: 700px) {
  .key {
    min-width: 36px;
    min-height: 38px;
    padding: 3px 5px;
    font-size: 14px;
  }

  .key.wide {
    min-width: 145px;
  }

  .key.action {
    min-width: 65px;
  }

  .key.confirm {
    min-width: 92px;
  }
}
</style>
