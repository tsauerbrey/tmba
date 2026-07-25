<script setup>
defineProps({
  coverUrl: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: 'TMBA-OS',
  },
})
</script>

<template>
  <div class="album-cover">
    <img
      v-if="coverUrl"
      class="album-cover__image"
      :src="coverUrl"
      :alt="`Albumcover: ${title}`"
    />

    <div v-else class="album-cover__placeholder">
      <span>♫</span>
      <small>TMBA-OS</small>
    </div>
  </div>
</template>

<style scoped>
.album-cover {
  width: min(100%, 280px);
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid #3a3e47;
  border-radius: 22px;
  background:
    radial-gradient(circle at 50% 35%, #174b78 0%, #0e2439 35%, #090d13 100%);
  box-shadow:
    0 15px 35px rgb(0 0 0 / 35%),
    0 0 22px rgb(22 140 255 / 10%);
}

.album-cover__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.album-cover__placeholder {
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
}
</style>