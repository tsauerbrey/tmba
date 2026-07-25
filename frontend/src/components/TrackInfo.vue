<script setup>
defineProps({
  title: {
    type: String,
    default: 'Keine Wiedergabe',
  },
  artist: {
    type: String,
    default: 'Quelle auswählen',
  },
  album: {
    type: String,
    default: 'TMBA-OS',
  },
})
</script>

<template>
  <section class="track-info">
    <span class="track-info__title">{{ title }}</span>

    <span class="track-info__separator">•</span>

    <span class="track-info__artist">{{ artist }}</span>

    <span class="track-info__separator">•</span>

    <span class="track-info__album">{{ album }}</span>
  </section>
</template>

<style scoped>
.track-info {
  display: flex;
  min-width: 0;
  min-height: 52px;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 18px;
  overflow: hidden;
  border: 1px solid #343841;
  border-radius: 18px;
  background:
    linear-gradient(
      145deg,
      rgb(31 34 40 / 96%),
      rgb(15 17 21 / 96%)
    );
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 4%),
    0 10px 25px rgb(0 0 0 / 20%);
  white-space: nowrap;
}

.track-info__title,
.track-info__artist,
.track-info__album {
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-info__title {
  color: #ffffff;
  font-size: 21px;
  font-weight: 800;
}

.track-info__artist {
  color: #168cff;
  font-size: 18px;
  font-weight: 700;
}

.track-info__album {
  color: #9297a1;
  font-size: 17px;
}

.track-info__separator {
  flex: 0 0 auto;
  color: #555b66;
  font-size: 18px;
}

@media (max-width: 700px) {
  .track-info {
    gap: 8px;
    padding-inline: 12px;
  }

  .track-info__title {
    font-size: 18px;
  }

  .track-info__artist,
  .track-info__album {
    font-size: 15px;
  }
}
</style>