from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class StationService:
    """Verwaltet dauerhaft gespeicherte Webradio-Sender."""

    DATA_FILE = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "radio_stations.json"
    )

    def __init__(self) -> None:
        self._lock = Lock()
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        """Legt die Senderdatei an, falls sie noch nicht existiert."""

        self.DATA_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.DATA_FILE.exists():
            return

        self._write_data_unlocked(
            {
                "stations": [],
            }
        )

    def _read_data_unlocked(self) -> dict[str, Any]:
        """Liest und prüft die gespeicherten Senderdaten."""

        try:
            with self.DATA_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                f"Senderdatei konnte nicht gelesen werden: {error}"
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                "Die Senderdatei muss ein JSON-Objekt enthalten."
            )

        stations = data.get("stations")

        if not isinstance(stations, list):
            raise RuntimeError(
                'Die Senderdatei benötigt eine Liste "stations".'
            )

        return data

    def _write_data_unlocked(
        self,
        data: dict[str, Any],
    ) -> None:
        """Speichert die Senderdaten atomar über eine temporäre Datei."""

        temporary_file = self.DATA_FILE.with_suffix(
            ".json.tmp"
        )

        try:
            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )
                file.write("\n")

            temporary_file.replace(self.DATA_FILE)

        except OSError as error:
            try:
                temporary_file.unlink(
                    missing_ok=True,
                )
            except OSError:
                pass

            raise RuntimeError(
                "Senderdatei konnte nicht gespeichert werden: "
                f"{error}"
            ) from error

    @staticmethod
    def _normalize_string_list(
        value: Any,
    ) -> list[str]:
        """Wandelt einen Wert in eine bereinigte Textliste um."""

        if isinstance(value, str):
            source_items = value.split(",")
        elif isinstance(value, list):
            source_items = value
        else:
            source_items = []

        result: list[str] = []
        known_items: set[str] = set()

        for item in source_items:
            normalized_item = str(
                item or ""
            ).strip()

            if not normalized_item:
                continue

            item_key = normalized_item.casefold()

            if item_key in known_items:
                continue

            known_items.add(item_key)
            result.append(normalized_item)

        return result

    @staticmethod
    def _normalize_int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _normalize_timestamp(value: Any) -> str:
        """Übernimmt nur sinnvoll aussehende ISO-Zeitstempel."""

        normalized_value = str(
            value or ""
        ).strip()

        if not normalized_value:
            return ""

        try:
            datetime.fromisoformat(
                normalized_value.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            return ""

        return normalized_value

    @staticmethod
    def _current_timestamp() -> str:
        """Erzeugt einen UTC-Zeitstempel im ISO-Format."""

        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

    @classmethod
    def _normalize_station(
        cls,
        station: dict[str, Any],
    ) -> dict[str, Any]:
        """Erzeugt eine einheitliche Senderdarstellung."""

        return {
            "id": str(
                station.get("id") or ""
            ).strip(),
            "name": str(
                station.get("name") or ""
            ).strip(),
            "url": str(
                station.get("url") or ""
            ).strip(),
            "favorite": bool(
                station.get("favorite", False)
            ),
            "logo_url": str(
                station.get("logo_url") or ""
            ).strip(),
            "provider": str(
                station.get("provider") or "local"
            ).strip(),
            "external_id": str(
                station.get("external_id") or ""
            ).strip(),
            "homepage": str(
                station.get("homepage") or ""
            ).strip(),
            "country": str(
                station.get("country") or ""
            ).strip(),
            "country_code": str(
                station.get("country_code") or ""
            ).strip().upper(),
            "state": str(
                station.get("state") or ""
            ).strip(),
            "languages": cls._normalize_string_list(
                station.get("languages")
            ),
            "tags": cls._normalize_string_list(
                station.get("tags")
            ),
            "codec": str(
                station.get("codec") or ""
            ).strip().upper(),
            "bitrate": max(
                0,
                cls._normalize_int(
                    station.get("bitrate"),
                    0,
                ),
            ),
            "last_played_at": cls._normalize_timestamp(
                station.get("last_played_at")
            ),
        }

    @staticmethod
    def _station_storage_data(
        station: dict[str, Any],
    ) -> dict[str, Any]:
        """Entfernt leere Zusatzfelder vor dem Speichern."""

        result: dict[str, Any] = {
            "id": station["id"],
            "name": station["name"],
            "url": station["url"],
            "favorite": station["favorite"],
            "logo_url": station["logo_url"],
        }

        optional_fields = (
            "provider",
            "external_id",
            "homepage",
            "country",
            "country_code",
            "state",
            "languages",
            "tags",
            "codec",
            "bitrate",
            "last_played_at",
        )

        for field_name in optional_fields:
            value = station.get(field_name)

            if value in (
                "",
                None,
                [],
                0,
            ):
                continue

            result[field_name] = value

        return result

    def list_stations(
        self,
        *,
        favorites_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Liefert alle Sender oder ausschließlich Favoriten."""

        with self._lock:
            data = self._read_data_unlocked()

        stations = [
            self._normalize_station(station)
            for station in data["stations"]
            if isinstance(station, dict)
        ]

        stations = [
            station
            for station in stations
            if (
                station["id"]
                and station["name"]
                and station["url"]
            )
        ]

        if favorites_only:
            stations = [
                station
                for station in stations
                if station["favorite"]
            ]

        return sorted(
            stations,
            key=lambda station: (
                not station["favorite"],
                station["name"].casefold(),
            ),
        )

    def get_station(
        self,
        station_id: str,
    ) -> dict[str, Any] | None:
        """Sucht einen Sender anhand seiner eindeutigen ID."""

        normalized_id = str(
            station_id or ""
        ).strip()

        if not normalized_id:
            return None

        for station in self.list_stations():
            if station["id"] == normalized_id:
                return station

        return None

    def set_favorite(
        self,
        station_id: str,
        favorite: bool,
    ) -> dict[str, Any] | None:
        """Setzt oder entfernt die Favoritenmarkierung."""

        normalized_id = str(
            station_id or ""
        ).strip()

        if not normalized_id:
            return None

        with self._lock:
            data = self._read_data_unlocked()
            updated_station: dict[str, Any] | None = None

            for station in data["stations"]:
                if not isinstance(
                    station,
                    dict,
                ):
                    continue

                current_id = str(
                    station.get("id") or ""
                ).strip()

                if current_id != normalized_id:
                    continue

                station["favorite"] = bool(
                    favorite
                )
                updated_station = (
                    self._normalize_station(
                        station
                    )
                )
                break

            if updated_station is None:
                return None

            self._write_data_unlocked(data)

        return updated_station

    def mark_played(
        self,
        station_id: str,
    ) -> dict[str, Any] | None:
        """Speichert den Zeitpunkt der letzten erfolgreichen Wiedergabe."""

        normalized_id = str(
            station_id or ""
        ).strip()

        if not normalized_id:
            return None

        with self._lock:
            data = self._read_data_unlocked()
            updated_station: dict[str, Any] | None = None

            for station in data["stations"]:
                if not isinstance(station, dict):
                    continue

                current_id = str(
                    station.get("id") or ""
                ).strip()

                if current_id != normalized_id:
                    continue

                station["last_played_at"] = (
                    self._current_timestamp()
                )
                updated_station = (
                    self._normalize_station(station)
                )
                break

            if updated_station is None:
                return None

            self._write_data_unlocked(data)

        return updated_station

    def delete_station(
        self,
        station_id: str,
    ) -> dict[str, Any] | None:
        """Löscht einen gespeicherten Sender."""

        normalized_id = str(
            station_id or ""
        ).strip()

        if not normalized_id:
            return None

        with self._lock:
            data = self._read_data_unlocked()
            deleted_station: dict[str, Any] | None = None
            remaining_stations: list[Any] = []

            for station in data["stations"]:
                if not isinstance(station, dict):
                    remaining_stations.append(station)
                    continue

                normalized_station = (
                    self._normalize_station(station)
                )

                if (
                    normalized_station["id"]
                    == normalized_id
                    and deleted_station is None
                ):
                    deleted_station = normalized_station
                    continue

                remaining_stations.append(station)

            if deleted_station is None:
                return None

            data["stations"] = remaining_stations
            self._write_data_unlocked(data)

        return deleted_station

    def import_online_station(
        self,
        station: dict[str, Any],
        *,
        favorite: bool = False,
    ) -> dict[str, Any]:
        """Importiert oder aktualisiert einen Online-Sender."""

        if not isinstance(station, dict):
            raise RuntimeError(
                "Die zu importierenden Senderdaten sind ungültig."
            )

        external_id = str(
            station.get("external_id") or ""
        ).strip()

        provider = str(
            station.get("provider")
            or "radio-browser"
        ).strip()

        station_id = (
            f"{provider}-{external_id}"
            if external_id
            else ""
        )

        imported_station = self._normalize_station(
            {
                "id": station_id,
                "name": station.get("name"),
                "url": (
                    station.get("stream_url")
                    or station.get("url")
                ),
                "favorite": favorite,
                "logo_url": station.get("logo_url"),
                "provider": provider,
                "external_id": external_id,
                "homepage": station.get("homepage"),
                "country": station.get("country"),
                "country_code": station.get(
                    "country_code"
                ),
                "state": station.get("state"),
                "languages": station.get(
                    "languages"
                ),
                "tags": station.get("tags"),
                "codec": station.get("codec"),
                "bitrate": station.get("bitrate"),
            }
        )

        if not imported_station["id"]:
            raise RuntimeError(
                "Der Online-Sender besitzt keine eindeutige ID."
            )

        if not imported_station["name"]:
            raise RuntimeError(
                "Der Online-Sender besitzt keinen Namen."
            )

        if not imported_station["url"]:
            raise RuntimeError(
                "Der Online-Sender besitzt keine Stream-URL."
            )

        with self._lock:
            data = self._read_data_unlocked()
            matching_index: int | None = None
            existing_favorite = False
            existing_last_played_at = ""

            for index, existing_station in enumerate(
                data["stations"]
            ):
                if not isinstance(
                    existing_station,
                    dict,
                ):
                    continue

                normalized_existing = (
                    self._normalize_station(
                        existing_station
                    )
                )

                same_id = (
                    normalized_existing["id"]
                    == imported_station["id"]
                )

                same_external_id = (
                    bool(external_id)
                    and normalized_existing[
                        "provider"
                    ] == provider
                    and normalized_existing[
                        "external_id"
                    ] == external_id
                )

                same_url = (
                    normalized_existing["url"]
                    == imported_station["url"]
                )

                if not (
                    same_id
                    or same_external_id
                    or same_url
                ):
                    continue

                matching_index = index
                existing_favorite = (
                    normalized_existing[
                        "favorite"
                    ]
                )
                existing_last_played_at = (
                    normalized_existing[
                        "last_played_at"
                    ]
                )
                break

            imported_station["favorite"] = (
                bool(favorite)
                or existing_favorite
            )
            imported_station["last_played_at"] = (
                existing_last_played_at
            )

            storage_data = (
                self._station_storage_data(
                    imported_station
                )
            )

            created = matching_index is None

            if created:
                data["stations"].append(
                    storage_data
                )
            else:
                data["stations"][
                    matching_index
                ] = storage_data

            self._write_data_unlocked(data)

        return {
            "created": created,
            "station": imported_station,
        }


station_service = StationService()
