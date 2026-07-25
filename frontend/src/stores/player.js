import { defineStore } from "pinia"

import {
  getStatus,
  nextPlayer,
  pausePlayer,
  playPlayer,
  previousPlayer,
  refreshPlayer,
  selectSource as selectSourceApi,
  stopPlayer,
  updateVolume,
} from "../api/player"


export const usePlayerStore = defineStore("player", {
  state: () => ({
    status: "idle",
    source: "none",
    volume: 50,

    track: {
      title: "Keine Wiedergabe",
      artist: "Quelle auswählen",
      album: "TMBA-OS",
      coverUrl: "",
      duration: 0,
      elapsed: 0,
    },

    loading: false,
    error: "",
  }),

  getters: {
    isPlaying: (state) => state.status === "play",
    isPaused: (state) => state.status === "pause",

    title: (state) => state.track.title,
    artist: (state) => state.track.artist,
    album: (state) => state.track.album,
    coverUrl: (state) => state.track.coverUrl,

    isLoading: (state) => state.loading,
    errorMessage: (state) => state.error,

    wifiConnected: () => true,
    bluetoothConnected: (state) =>
      state.source === "bluetooth",
  },

  actions: {
    applyStatus(data) {
      this.status = data.status ?? "idle"
      this.source = data.source ?? "none"
      this.volume = Number(data.volume ?? 50)

      const track = data.track ?? {}

      this.track = {
        title: track.title ?? "Keine Wiedergabe",
        artist: track.artist ?? "",
        album: track.album ?? "",
        coverUrl: track.cover_url ?? "",
        duration: Number(track.duration ?? 0),
        elapsed: Number(track.elapsed ?? 0),
      }
    },

    async runPlayerAction(action) {
      this.loading = true
      this.error = ""

      try {
        const data = await action()
        this.applyStatus(data)
        return data
      } catch (error) {
        this.error =
          error instanceof Error
            ? error.message
            : "Unbekannter Player-Fehler"

        console.error(error)
        return null
      } finally {
        this.loading = false
      }
    },

    async loadStatus() {
      return this.runPlayerAction(() => getStatus())
    },

    async refresh() {
      return this.runPlayerAction(() => refreshPlayer())
    },

    async setVolume(volume) {
      return this.runPlayerAction(() => updateVolume(volume))
    },

    async decreaseVolume() {
      return this.setVolume(this.volume - 5)
    },

    async increaseVolume() {
      return this.setVolume(this.volume + 5)
    },

    async selectSource(source) {
      return this.runPlayerAction(() => selectSourceApi(source))
    },

    async previous() {
      return this.runPlayerAction(() => previousPlayer())
    },

    async stop() {
      return this.runPlayerAction(() => stopPlayer())
    },

    async pause() {
      return this.runPlayerAction(() => pausePlayer())
    },

    async play() {
      return this.runPlayerAction(() => playPlayer())
    },

    async next() {
      return this.runPlayerAction(() => nextPlayer())
    },

    async togglePlayback() {
      if (this.isPlaying) {
        return this.pause()
      }

      return this.play()
    },
  },
})