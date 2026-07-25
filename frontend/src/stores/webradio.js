import { defineStore } from 'pinia'

import {
  deleteWebradioStation,
  getWebradioStations,
  importOnlineWebradioStation,
  playOnlineWebradioStation,
  playWebradioStation,
  searchOnlineWebradioStations,
  setWebradioFavorite,
} from '../api/webradio'


function errorMessage(
  error,
  fallback,
) {
  return error instanceof Error
    ? error.message
    : fallback
}


function sortStations(stations) {
  return [...stations].sort(
    (first, second) => {
      if (first.favorite !== second.favorite) {
        return first.favorite ? -1 : 1
      }

      return String(first.name || '').localeCompare(
        String(second.name || ''),
        'de',
      )
    },
  )
}


export const useWebradioStore = defineStore(
  'webradio',
  {
    state: () => ({
      stations: [],
      selectedStationId: '',

      loading: false,
      error: '',
      deletingStationId: '',

      onlineStations: [],
      onlineLoading: false,
      onlineError: '',
      onlineSearched: false,

      importingStationId: '',
      previewingStationId: '',

      onlineQuery: {
        query: '',
        countryCode: 'DE',
        tag: '',
        language: '',
        minimumBitrate: 0,
        limit: 30,
      },
    }),

    getters: {
      selectedStation(state) {
        return (
          state.stations.find(
            station =>
              station.id
              === state.selectedStationId,
          ) ?? null
        )
      },

      favoriteStations(state) {
        return state.stations.filter(
          station => station.favorite,
        )
      },

      recentStations(state) {
        return [...state.stations]
          .filter(
            station =>
              Boolean(station.last_played_at),
          )
          .sort(
            (first, second) =>
              String(
                second.last_played_at || '',
              ).localeCompare(
                String(
                  first.last_played_at || '',
                ),
              ),
          )
      },

      importedExternalIds(state) {
        return new Set(
          state.stations
            .map(
              station =>
                station.external_id || '',
            )
            .filter(Boolean),
        )
      },
    },

    actions: {
      async loadStations() {
        this.loading = true
        this.error = ''

        try {
          const data =
            await getWebradioStations()

          this.stations = sortStations(
            Array.isArray(data?.stations)
              ? data.stations
              : [],
          )

          if (
            this.selectedStationId
            && !this.stations.some(
              station =>
                station.id
                === this.selectedStationId,
            )
          ) {
            this.selectedStationId = ''
          }

          if (
            !this.selectedStationId
            && this.stations.length > 0
          ) {
            this.selectedStationId =
              this.stations[0].id
          }

          return data
        } catch (error) {
          this.error = errorMessage(
            error,
            'Senderliste konnte nicht geladen werden.',
          )

          console.error(error)
          return null
        } finally {
          this.loading = false
        }
      },

      selectStation(stationId) {
        this.selectedStationId = stationId
      },

      async playStation(stationId) {
        this.loading = true
        this.error = ''

        try {
          this.selectedStationId = stationId

          const data =
            await playWebradioStation(
              stationId,
            )

          if (data?.station) {
            this.stations = sortStations(
              this.stations.map(
                station =>
                  station.id === data.station.id
                    ? data.station
                    : station,
              ),
            )
          }

          return data
        } catch (error) {
          this.error = errorMessage(
            error,
            'Sender konnte nicht gestartet werden.',
          )

          console.error(error)
          return null
        } finally {
          this.loading = false
        }
      },

      async deleteStation(stationId) {
        this.deletingStationId = stationId
        this.error = ''

        try {
          const data =
            await deleteWebradioStation(
              stationId,
            )

          this.stations = this.stations.filter(
            station =>
              station.id !== stationId,
          )

          if (
            this.selectedStationId
            === stationId
          ) {
            this.selectedStationId =
              this.stations[0]?.id || ''
          }

          return data
        } catch (error) {
          this.error = errorMessage(
            error,
            'Sender konnte nicht gelöscht werden.',
          )

          console.error(error)
          return null
        } finally {
          this.deletingStationId = ''
        }
      },

      async playOnlineStation(station) {
        const stationId =
          station.external_id
          || station.stream_url

        if (!stationId) {
          return null
        }

        this.previewingStationId = stationId
        this.onlineError = ''

        try {
          return await playOnlineWebradioStation(
            station,
          )
        } catch (error) {
          this.onlineError = errorMessage(
            error,
            'Online-Sender konnte nicht gestartet werden.',
          )

          console.error(error)
          return null
        } finally {
          this.previewingStationId = ''
        }
      },

      async toggleFavorite(stationId) {
        const station = this.stations.find(
          item => item.id === stationId,
        )

        if (!station) {
          return null
        }

        this.loading = true
        this.error = ''

        try {
          const data =
            await setWebradioFavorite(
              stationId,
              !station.favorite,
            )

          const updatedStation = data.station

          this.stations = sortStations(
            this.stations.map(
              item =>
                item.id === updatedStation.id
                  ? updatedStation
                  : item,
            ),
          )

          return data
        } catch (error) {
          this.error = errorMessage(
            error,
            'Favorit konnte nicht geändert werden.',
          )

          console.error(error)
          return null
        } finally {
          this.loading = false
        }
      },

      async searchOnlineStations(
        searchOptions = {},
      ) {
        this.onlineLoading = true
        this.onlineError = ''
        this.onlineSearched = true

        this.onlineQuery = {
          ...this.onlineQuery,
          ...searchOptions,
        }

        try {
          const data =
            await searchOnlineWebradioStations(
              this.onlineQuery,
            )

          this.onlineStations =
            Array.isArray(data?.stations)
              ? data.stations
              : []

          return data
        } catch (error) {
          this.onlineStations = []

          this.onlineError = errorMessage(
            error,
            'Online-Suche konnte nicht ausgeführt werden.',
          )

          console.error(error)
          return null
        } finally {
          this.onlineLoading = false
        }
      },

      async importOnlineStation(
        station,
        favorite = false,
      ) {
        const stationUuid =
          station.external_id || ''

        if (!stationUuid) {
          this.onlineError =
            'Der Online-Sender besitzt keine gültige ID.'

          return null
        }

        this.importingStationId = stationUuid
        this.onlineError = ''

        try {
          const data =
            await importOnlineWebradioStation(
              stationUuid,
              favorite,
            )

          await this.loadStations()

          if (data?.station?.id) {
            this.selectedStationId =
              data.station.id
          }

          return data
        } catch (error) {
          this.onlineError = errorMessage(
            error,
            'Sender konnte nicht importiert werden.',
          )

          console.error(error)
          return null
        } finally {
          this.importingStationId = ''
        }
      },

      clearOnlineSearch() {
        this.onlineStations = []
        this.onlineError = ''
        this.onlineSearched = false
      },
    },
  },
)
