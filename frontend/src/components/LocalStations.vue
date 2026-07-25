<script setup>
import {
  computed,
  onMounted,
  ref,
} from 'vue'
import { storeToRefs } from 'pinia'

import { usePlayerStore } from '../stores/player'
import { useWebradioStore } from '../stores/webradio'

const playerStore = usePlayerStore()
const webradioStore = useWebradioStore()

const {
  stations,
  selectedStationId,
  loading,
  error,
  deletingStationId,
} = storeToRefs(webradioStore)

const searchText = ref('')
const selectedFilter = ref('all')
const playingStationId = ref('')
const stationToDelete = ref(null)
const failedLogos = ref(new Set())

const favoriteCount = computed(() => {
  return stations.value.filter(
    station => station.favorite,
  ).length
})

const recentCount = computed(() => {
  return stations.value.filter(
    station => station.last_played_at,
  ).length
})

const filteredStations = computed(() => {
  const search = searchText.value
    .trim()
    .toLocaleLowerCase('de')

  let result = stations.value.filter((station) => {
    if (
      selectedFilter.value === 'favorites'
      && !station.favorite
    ) {
      return false
    }

    if (
      selectedFilter.value === 'recent'
      && !station.last_played_at
    ) {
      return false
    }

    if (!search) {
      return true
    }

    const searchableText = [
      station.name,
      station.country,
      station.state,
      station.codec,
      ...(Array.isArray(station.tags)
        ? station.tags
        : []),
      ...(Array.isArray(station.languages)
        ? station.languages
        : []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLocaleLowerCase('de')

    return searchableText.includes(search)
  })

  if (selectedFilter.value === 'recent') {
    result = [...result].sort(
      (first, second) =>
        String(
          second.last_played_at || '',
        ).localeCompare(
          String(
            first.last_played_at || '',
          ),
        ),
    )
  }

  return result
})

const resultLabel = computed(() => {
  const count = filteredStations.value.length

  return count === 1
    ? '1 Sender'
    : `${count} Sender`
})

function selectFilter(filterName) {
  selectedFilter.value = filterName
}

function selectStation(station) {
  webradioStore.selectStation(station.id)
}

function logoIsAvailable(station) {
  return Boolean(
    station.logo_url
    && !failedLogos.value.has(station.id),
  )
}

function handleLogoError(station) {
  const nextFailedLogos = new Set(
    failedLogos.value,
  )

  nextFailedLogos.add(station.id)
  failedLogos.value = nextFailedLogos
}

function formatLastPlayed(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat(
    'de-DE',
    {
      dateStyle: 'short',
      timeStyle: 'short',
    },
  ).format(date)
}

function stationSubtitle(station) {
  if (
    selectedFilter.value === 'recent'
    && station.last_played_at
  ) {
    return `Zuletzt: ${formatLastPlayed(
      station.last_played_at,
    )}`
  }

  if (
    selectedStationId.value
    === station.id
  ) {
    return 'Ausgewählt'
  }

  const details = []

  if (
    Array.isArray(station.tags)
    && station.tags.length > 0
  ) {
    details.push(station.tags[0])
  }

  if (station.country) {
    details.push(station.country)
  }

  if (station.codec) {
    details.push(
      station.bitrate
        ? `${station.codec} · ${station.bitrate} kbit/s`
        : station.codec,
    )
  }

  return details.join(' · ') || 'Webradio'
}

async function playStation(station) {
  if (playingStationId.value) {
    return
  }

  playingStationId.value = station.id
  webradioStore.selectStation(station.id)

  try {
    const result =
      await webradioStore.playStation(
        station.id,
      )

    if (result?.player) {
      playerStore.applyStatus(
        result.player,
      )
    }
  } finally {
    playingStationId.value = ''
  }
}

async function toggleFavorite(station) {
  await webradioStore.toggleFavorite(
    station.id,
  )
}

function requestDelete(station) {
  stationToDelete.value = station
}

function cancelDelete() {
  if (!deletingStationId.value) {
    stationToDelete.value = null
  }
}

async function confirmDelete() {
  const station = stationToDelete.value

  if (!station) {
    return
  }

  const result =
    await webradioStore.deleteStation(
      station.id,
    )

  if (result) {
    stationToDelete.value = null
  }
}

onMounted(() => {
  if (stations.value.length === 0) {
    webradioStore.loadStations()
  }
})
</script>

<template>
  <section class="local-stations">
    <div class="local-stations__toolbar">
      <div class="local-stations__filters">
        <button
          type="button"
          class="local-stations__filter"
          :class="{
            'local-stations__filter--active':
              selectedFilter === 'all',
          }"
          @click="selectFilter('all')"
        >
          Alle
          <span>{{ stations.length }}</span>
        </button>

        <button
          type="button"
          class="local-stations__filter"
          :class="{
            'local-stations__filter--active':
              selectedFilter === 'favorites',
          }"
          @click="selectFilter('favorites')"
        >
          Favoriten
          <span>{{ favoriteCount }}</span>
        </button>

        <button
          type="button"
          class="local-stations__filter"
          :class="{
            'local-stations__filter--active':
              selectedFilter === 'recent',
          }"
          @click="selectFilter('recent')"
        >
          Zuletzt
          <span>{{ recentCount }}</span>
        </button>
      </div>

      <label class="local-stations__search">
        <span aria-hidden="true">⌕</span>
        <input
          v-model="searchText"
          type="search"
          placeholder="Gespeicherte Sender durchsuchen"
          autocomplete="off"
        >
      </label>
    </div>

    <p
      v-if="error"
      class="local-stations__error"
    >
      {{ error }}
    </p>

    <div
      v-if="loading && stations.length === 0"
      class="local-stations__message"
    >
      Sender werden geladen …
    </div>

    <div
      v-else-if="filteredStations.length === 0"
      class="local-stations__message"
    >
      <strong>Keine Sender gefunden</strong>
      <span>
        Passe Suche oder Filter an.
      </span>
    </div>

    <div
      v-else
      class="local-stations__list"
    >
      <article
        v-for="station in filteredStations"
        :key="station.id"
        class="station"
        :class="{
          'station--selected':
            selectedStationId === station.id,
        }"
        @click="selectStation(station)"
      >
        <div class="station__logo">
          <img
            v-if="logoIsAvailable(station)"
            :src="station.logo_url"
            :alt="`${station.name} Logo`"
            @error="handleLogoError(station)"
          >
          <span v-else aria-hidden="true">♪</span>
        </div>

        <div class="station__text">
          <strong>{{ station.name }}</strong>
          <span>{{ stationSubtitle(station) }}</span>
        </div>

        <button
          type="button"
          class="station__favorite"
          :aria-label="
            station.favorite
              ? `${station.name} aus Favoriten entfernen`
              : `${station.name} zu Favoriten hinzufügen`
          "
          @click.stop="toggleFavorite(station)"
        >
          {{ station.favorite ? '★' : '☆' }}
        </button>

        <button
          type="button"
          class="station__delete"
          :disabled="
            deletingStationId === station.id
          "
          :aria-label="`${station.name} löschen`"
          @click.stop="requestDelete(station)"
        >
          🗑
        </button>

        <button
          type="button"
          class="station__play"
          :disabled="
            Boolean(playingStationId)
            || deletingStationId === station.id
          "
          :aria-label="`${station.name} abspielen`"
          @click.stop="playStation(station)"
        >
          <span
            v-if="
              playingStationId === station.id
            "
            class="station__spinner"
          />
          <span v-else aria-hidden="true">▶</span>
        </button>
      </article>
    </div>

    <footer class="local-stations__footer">
      {{ resultLabel }}
    </footer>

    <div
      v-if="stationToDelete"
      class="delete-dialog-backdrop"
      @click.self="cancelDelete"
    >
      <section
        class="delete-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-dialog-title"
      >
        <span
          class="delete-dialog__icon"
          aria-hidden="true"
        >
          🗑
        </span>

        <h3 id="delete-dialog-title">
          Sender löschen?
        </h3>

        <p>
          „{{ stationToDelete.name }}“ wird dauerhaft
          aus den gespeicherten Sendern entfernt.
        </p>

        <div class="delete-dialog__actions">
          <button
            type="button"
            class="delete-dialog__cancel"
            :disabled="Boolean(deletingStationId)"
            @click="cancelDelete"
          >
            Abbrechen
          </button>

          <button
            type="button"
            class="delete-dialog__confirm"
            :disabled="Boolean(deletingStationId)"
            @click="confirmDelete"
          >
            {{
              deletingStationId
                ? 'Wird gelöscht …'
                : 'Löschen'
            }}
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.local-stations {
  display: flex;
  min-height: 0;
  flex: 1 1 auto;
  flex-direction: column;
}

.local-stations__toolbar {
  display: grid;
  grid-template-columns: auto minmax(220px, 1fr);
  gap: 10px;
  margin-bottom: 9px;
}

.local-stations__filters {
  display: flex;
  gap: 6px;
}

.local-stations__filter {
  min-height: 38px;
  padding: 6px 10px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 11px;
  background: rgb(255 255 255 / 5%);
  color: #bec4cc;
  cursor: pointer;
  font-size: 12px;
  font-weight: 750;
}

.local-stations__filter span {
  margin-left: 4px;
  color: #858c95;
}

.local-stations__filter--active {
  border-color: rgb(128 196 59 / 55%);
  background: rgb(128 196 59 / 15%);
  color: #e7ffd1;
}

.local-stations__search {
  display: flex;
  min-height: 38px;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 11px;
  background: rgb(255 255 255 / 5%);
}

.local-stations__search span {
  color: #8d949d;
  font-size: 21px;
}

.local-stations__search input {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #fff;
}

.local-stations__search input::placeholder {
  color: #777f89;
}

.local-stations__list {
  display: grid;
  min-height: 0;
  flex: 1 1 auto;
  gap: 7px;
  overflow-y: auto;
  padding-right: 3px;
}

.station {
  display: grid;
  grid-template-columns:
    52px
    minmax(0, 1fr)
    42px
    42px
    46px;
  align-items: center;
  gap: 8px;
  padding: 7px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 14px;
  background: rgb(255 255 255 / 4%);
  cursor: pointer;
  transition:
    border-color 140ms ease,
    background 140ms ease;
}

.station--selected {
  border-color: rgb(128 196 59 / 40%);
  background: rgb(128 196 59 / 8%);
}

.station__logo {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  overflow: hidden;
  border-radius: 11px;
  background: #202329;
  color: #80c43b;
  font-size: 25px;
}

.station__logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.station__text {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.station__text strong,
.station__text span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.station__text strong {
  color: #f1f3f5;
  font-size: 14px;
}

.station__text span {
  color: #9097a0;
  font-size: 11px;
}

.station__favorite,
.station__delete,
.station__play {
  display: grid;
  border: 0;
  place-items: center;
  cursor: pointer;
}

.station__favorite,
.station__delete {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: transparent;
}

.station__favorite {
  color: #ffd86a;
  font-size: 25px;
}

.station__delete {
  color: #ff9b9b;
  font-size: 18px;
}

.station__delete:active:not(:disabled),
.station__favorite:active:not(:disabled) {
  background: rgb(255 255 255 / 8%);
  transform: scale(0.92);
}

.station__play {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #80c43b;
  color: #10130d;
  box-shadow: 0 5px 18px rgb(128 196 59 / 25%);
}

.station__play:active:not(:disabled) {
  transform: scale(0.92);
}

.station__spinner {
  width: 19px;
  height: 19px;
  border: 3px solid rgb(16 19 13 / 25%);
  border-top-color: #10130d;
  border-radius: 50%;
  animation: spin 800ms linear infinite;
}

.local-stations__message {
  display: flex;
  min-height: 140px;
  flex: 1 1 auto;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #8f969f;
  text-align: center;
}

.local-stations__message strong {
  color: #dce0e5;
}

.local-stations__error {
  margin: 0 0 8px;
  padding: 9px 11px;
  border-radius: 10px;
  background: rgb(136 39 39 / 55%);
  color: #ffdede;
  font-size: 12px;
}

.local-stations__footer {
  margin-top: 7px;
  color: #858c95;
  font-size: 11px;
}

.delete-dialog-backdrop {
  position: fixed;
  z-index: 1000;
  display: grid;
  padding: 18px;
  background: rgb(0 0 0 / 72%);
  inset: 0;
  place-items: center;
}

.delete-dialog {
  width: min(100%, 410px);
  padding: 24px;
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 20px;
  background: #24272d;
  box-shadow: 0 24px 70px rgb(0 0 0 / 55%);
  text-align: center;
}

.delete-dialog__icon {
  display: block;
  margin-bottom: 8px;
  font-size: 34px;
}

.delete-dialog h3 {
  margin: 0;
  color: #fff;
  font-size: 21px;
}

.delete-dialog p {
  margin: 12px 0 20px;
  color: #aeb4bd;
  line-height: 1.45;
}

.delete-dialog__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.delete-dialog__actions button {
  min-height: 43px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 800;
}

.delete-dialog__cancel {
  border: 1px solid rgb(255 255 255 / 12%);
  background: rgb(255 255 255 / 6%);
  color: #e3e6ea;
}

.delete-dialog__confirm {
  border: 1px solid rgb(255 112 112 / 45%);
  background: rgb(168 48 48 / 70%);
  color: #fff;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 680px) {
  .local-stations__toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-height: 520px) {
  .local-stations__toolbar {
    grid-template-columns: auto minmax(190px, 1fr);
    gap: 7px;
    margin-bottom: 6px;
  }

  .local-stations__filter {
    min-height: 32px;
    padding: 4px 8px;
  }

  .local-stations__search {
    min-height: 32px;
  }

  .station {
    grid-template-columns:
      44px
      minmax(0, 1fr)
      36px
      36px
      40px;
    gap: 5px;
    padding: 5px;
  }

  .station__logo {
    width: 44px;
    height: 44px;
  }

  .station__favorite,
  .station__delete {
    width: 34px;
    height: 34px;
  }

  .station__play {
    width: 38px;
    height: 38px;
  }

  .delete-dialog {
    padding: 18px;
  }
}
</style>
