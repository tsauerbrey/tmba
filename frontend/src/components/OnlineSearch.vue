<script setup>
import {
  computed,
  ref,
} from 'vue'
import { storeToRefs } from 'pinia'

import { usePlayerStore } from '../stores/player'
import { useWebradioStore } from '../stores/webradio'

const playerStore = usePlayerStore()
const webradioStore = useWebradioStore()

const {
  onlineStations,
  onlineLoading,
  onlineError,
  onlineSearched,
  importingStationId,
  previewingStationId,
  importedExternalIds,
} = storeToRefs(webradioStore)

const searchText = ref('')
const countryCode = ref('DE')
const failedLogos = ref(new Set())
const successMessage = ref('')

const resultLabel = computed(() => {
  const count = onlineStations.value.length

  return count === 1
    ? '1 Treffer'
    : `${count} Treffer`
})

function logoIsAvailable(station) {
  const key =
    station.external_id
    || station.stream_url

  return Boolean(
    station.logo_url
    && !failedLogos.value.has(key),
  )
}

function handleLogoError(station) {
  const key =
    station.external_id
    || station.stream_url

  const nextFailedLogos = new Set(
    failedLogos.value,
  )

  nextFailedLogos.add(key)
  failedLogos.value = nextFailedLogos
}

function isImported(station) {
  return importedExternalIds.value.has(
    station.external_id,
  )
}

function stationSubtitle(station) {
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

  return details.join(' · ') || 'Online-Radio'
}

async function search() {
  successMessage.value = ''

  if (
    !searchText.value.trim()
    && !countryCode.value.trim()
  ) {
    return
  }

  await webradioStore.searchOnlineStations({
    query: searchText.value,
    countryCode: countryCode.value,
    limit: 30,
  })
}

async function preview(station) {
  successMessage.value = ''

  const result =
    await webradioStore.playOnlineStation(
      station,
    )

  if (result?.player) {
    playerStore.applyStatus(result.player)
  }
}

async function importStation(station) {
  successMessage.value = ''

  const result =
    await webradioStore.importOnlineStation(
      station,
      false,
    )

  if (result?.success) {
    successMessage.value = result.created
      ? `${station.name} wurde gespeichert.`
      : `${station.name} war bereits gespeichert und wurde aktualisiert.`
  }
}
</script>

<template>
  <section class="online">
    <form
      class="online__form"
      @submit.prevent="search"
    >
      <label class="online__search">
        <span aria-hidden="true">⌕</span>

        <input
          v-model="searchText"
          type="search"
          placeholder="Sendername, z. B. Bayern 3"
          autocomplete="off"
        >
      </label>

      <label class="online__country">
        <span>Land</span>

        <select v-model="countryCode">
          <option value="DE">DE</option>
          <option value="AT">AT</option>
          <option value="CH">CH</option>
          <option value="GB">GB</option>
          <option value="US">US</option>
          <option value="">Alle</option>
        </select>
      </label>

      <button
        class="online__submit"
        type="submit"
        :disabled="onlineLoading"
      >
        <span
          v-if="onlineLoading"
          class="spinner spinner--button"
        ></span>

        <span v-else>Suchen</span>
      </button>
    </form>

    <div class="online__status-row">
      <span>
        {{
          onlineSearched
            ? resultLabel
            : 'Radio Browser'
        }}
      </span>

      <button
        v-if="
          onlineSearched
          && onlineStations.length > 0
        "
        type="button"
        @click="webradioStore.clearOnlineSearch()"
      >
        Ergebnisse löschen
      </button>
    </div>

    <p
      v-if="successMessage"
      class="online__success"
    >
      {{ successMessage }}
    </p>

    <div
      v-if="onlineError"
      class="online__message online__message--error"
    >
      <strong>Online-Suche fehlgeschlagen</strong>
      <span>{{ onlineError }}</span>
    </div>

    <div
      v-else-if="onlineLoading"
      class="online__message"
    >
      <span class="spinner"></span>
      Online-Sender werden gesucht …
    </div>

    <div
      v-else-if="!onlineSearched"
      class="online__message"
    >
      <span class="online__empty">⌕</span>
      <strong>Online-Sender suchen</strong>

      <span>
        Suche nach Sendernamen in der öffentlichen
        Radio-Browser-Datenbank.
      </span>
    </div>

    <div
      v-else-if="onlineStations.length === 0"
      class="online__message"
    >
      <span class="online__empty">◎</span>
      <strong>Keine Sender gefunden</strong>

      <span>
        Ändere den Suchbegriff oder das Land.
      </span>
    </div>

    <div
      v-else
      class="online-list"
    >
      <article
        v-for="station in onlineStations"
        :key="
          station.external_id
          || station.stream_url
        "
        class="online-station"
      >
        <div class="online-station__logo">
          <img
            v-if="logoIsAvailable(station)"
            :src="station.logo_url"
            :alt="`${station.name} Logo`"
            @error="handleLogoError(station)"
          >

          <span v-else>◎</span>
        </div>

        <div class="online-station__text">
          <strong>{{ station.name }}</strong>
          <small>
            {{ stationSubtitle(station) }}
          </small>
        </div>

        <button
          class="online-station__import"
          :class="{
            'online-station__import--done':
              isImported(station),
          }"
          type="button"
          :disabled="
            Boolean(importingStationId)
            || isImported(station)
          "
          :aria-label="
            isImported(station)
              ? `${station.name} ist gespeichert`
              : `${station.name} speichern`
          "
          @click="importStation(station)"
        >
          <span
            v-if="
              importingStationId
              === station.external_id
            "
            class="spinner spinner--small"
          ></span>

          <span v-else-if="isImported(station)">
            ✓
          </span>

          <span v-else>＋</span>
        </button>

        <button
          class="online-station__play"
          type="button"
          :disabled="Boolean(previewingStationId)"
          @click="preview(station)"
        >
          <span
            v-if="
              previewingStationId
              === (
                station.external_id
                || station.stream_url
              )
            "
            class="spinner spinner--small"
          ></span>

          <span v-else>▶</span>
        </button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.online {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

.online__form {
  display: grid;
  grid-template-columns:
    minmax(0, 1fr)
    86px
    92px;
  gap: 8px;
  margin-bottom: 7px;
}

.online__search {
  display: flex;
  min-width: 0;
  min-height: 43px;
  align-items: center;
  gap: 9px;
  padding: 0 12px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 12px;
  background: rgb(0 0 0 / 22%);
}

.online__search:focus-within {
  border-color: rgb(128 196 59 / 52%);
}

.online__search span {
  color: #aeb4bd;
  font-size: 22px;
}

.online__search input {
  width: 100%;
  min-width: 0;
  padding: 8px 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #fff;
  font-size: 15px;
}

.online__country {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4px 8px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 12px;
  background: rgb(0 0 0 / 22%);
}

.online__country span {
  color: #838a93;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
}

.online__country select {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #fff;
  font-size: 14px;
  font-weight: 750;
}

.online__submit {
  min-height: 43px;
  border: 1px solid rgb(128 196 59 / 60%);
  border-radius: 12px;
  background: #80c43b;
  color: #11140e;
  cursor: pointer;
  font-weight: 850;
}

.online__status-row {
  display: flex;
  min-height: 28px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #8e959f;
  font-size: 11px;
  font-weight: 700;
}

.online__status-row button {
  border: 0;
  background: transparent;
  color: #9fcf70;
  cursor: pointer;
  font-size: 11px;
}

.online__success {
  margin: 3px 0 7px;
  padding: 7px 10px;
  border: 1px solid rgb(128 196 59 / 30%);
  border-radius: 10px;
  background: rgb(128 196 59 / 10%);
  color: #c9f3a1;
  font-size: 12px;
}

.online-list {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  padding-right: 3px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
}

.online-station {
  display: grid;
  grid-template-columns:
    50px
    minmax(0, 1fr)
    42px
    46px;
  align-items: center;
  gap: 9px;
  padding: 7px;
  border: 1px solid transparent;
  border-radius: 14px;
  background: rgb(255 255 255 / 5%);
}

.online-station__logo {
  display: flex;
  width: 50px;
  height: 50px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 11px;
  background: #15171a;
  color: #80c43b;
  font-size: 27px;
}

.online-station__logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #fff;
}

.online-station__text {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.online-station__text strong,
.online-station__text small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.online-station__text strong {
  color: #f2f5f7;
  font-size: 15px;
}

.online-station__text small {
  color: #a5abb4;
  font-size: 11px;
}

.online-station__import,
.online-station__play {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  cursor: pointer;
}

.online-station__import {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgb(255 255 255 / 8%);
  color: #d7dce2;
  font-size: 25px;
}

.online-station__import--done {
  background: rgb(128 196 59 / 16%);
  color: #aee278;
}

.online-station__play {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #80c43b;
  color: #10130d;
  font-size: 17px;
}

.online__message {
  display: flex;
  min-height: 140px;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 20px;
  color: #b5bac2;
  text-align: center;
}

.online__message--error {
  color: #ffb3b3;
}

.online__empty {
  color: #80c43b;
  font-size: 36px;
}

.spinner {
  width: 31px;
  height: 31px;
  border: 4px solid rgb(255 255 255 / 12%);
  border-top-color: #80c43b;
  border-radius: 50%;
  animation: spin 800ms linear infinite;
}

.spinner--button {
  width: 19px;
  height: 19px;
  border-width: 3px;
  border-color: rgb(16 19 13 / 25%);
  border-top-color: #10130d;
}

.spinner--small {
  width: 18px;
  height: 18px;
  border-width: 3px;
  border-color: rgb(255 255 255 / 20%);
  border-top-color: currentColor;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-height: 520px) {
  .online__form {
    grid-template-columns:
      minmax(0, 1fr)
      76px
      82px;
    gap: 6px;
  }

  .online__search,
  .online__submit {
    min-height: 38px;
  }

  .online-station {
    grid-template-columns:
      45px
      minmax(0, 1fr)
      38px
      41px;
    gap: 7px;
    padding: 5px;
  }

  .online-station__logo {
    width: 45px;
    height: 45px;
  }

  .online-station__import {
    width: 36px;
    height: 36px;
  }

  .online-station__play {
    width: 38px;
    height: 38px;
  }
}
</style>