from __future__ import annotations

import random
from typing import Any

import httpx


class RadioBrowserError(RuntimeError):
    """Fehler bei der Kommunikation mit Radio Browser."""


class RadioBrowserService:
    """Sucht Webradio-Sender in der öffentlichen Radio-Browser-Datenbank."""

    API_SERVERS = (
        "https://de1.api.radio-browser.info",
        "https://de2.api.radio-browser.info",
        "https://fi1.api.radio-browser.info",
    )

    SEARCH_PATH = "/json/stations/search"

    USER_AGENT = "TMBA-OS/0.1.0"

    def __init__(
        self,
        *,
        timeout: float = 8.0,
    ) -> None:
        self.timeout = timeout

    async def search_stations(
        self,
        *,
        query: str = "",
        country_code: str = "",
        tag: str = "",
        language: str = "",
        minimum_bitrate: int = 0,
        limit: int = 30,
    ) -> dict[str, Any]:
        """
        Sucht Stationen in der Radio-Browser-Datenbank.

        Die Suche kann über Sendername, Land, Tag und Sprache
        eingeschränkt werden.
        """

        normalized_query = str(query or "").strip()
        normalized_country_code = (
            str(country_code or "")
            .strip()
            .upper()
        )
        normalized_tag = str(tag or "").strip()
        normalized_language = str(language or "").strip()

        normalized_limit = max(
            1,
            min(100, int(limit)),
        )

        normalized_minimum_bitrate = max(
            0,
            min(10000, int(minimum_bitrate)),
        )

        if (
            not normalized_query
            and not normalized_country_code
            and not normalized_tag
            and not normalized_language
        ):
            raise RadioBrowserError(
                "Bitte gib mindestens einen Suchbegriff, "
                "ein Land, ein Genre oder eine Sprache an."
            )

        parameters: dict[str, str | int] = {
            "hidebroken": "true",
            "order": "votes",
            "reverse": "true",
            "limit": normalized_limit,
        }

        if normalized_query:
            parameters["name"] = normalized_query

        if normalized_country_code:
            parameters["countrycode"] = normalized_country_code

        if normalized_tag:
            parameters["tag"] = normalized_tag

        if normalized_language:
            parameters["language"] = normalized_language

        if normalized_minimum_bitrate > 0:
            parameters["bitrateMin"] = normalized_minimum_bitrate

        raw_stations, server = await self._request_json(
            path=self.SEARCH_PATH,
            parameters=parameters,
        )

        if not isinstance(raw_stations, list):
            raise RadioBrowserError(
                "Radio Browser hat ein unerwartetes Datenformat geliefert."
            )

        stations: list[dict[str, Any]] = []
        known_station_keys: set[str] = set()

        for raw_station in raw_stations:
            if not isinstance(raw_station, dict):
                continue

            station = self._normalize_station(raw_station)

            if station is None:
                continue

            station_key = (
                station["external_id"]
                or station["stream_url"]
            )

            if station_key in known_station_keys:
                continue

            known_station_keys.add(station_key)
            stations.append(station)

        return {
            "success": True,
            "query": {
                "text": normalized_query,
                "country_code": normalized_country_code,
                "tag": normalized_tag,
                "language": normalized_language,
                "minimum_bitrate": normalized_minimum_bitrate,
                "limit": normalized_limit,
            },
            "count": len(stations),
            "stations": stations,
            "provider": {
                "name": "Radio Browser",
                "server": server,
            },
        }

    async def get_station(
        self,
        station_uuid: str,
    ) -> dict[str, Any] | None:
        """Lädt eine einzelne Station anhand ihrer Radio-Browser-UUID."""

        normalized_uuid = str(station_uuid or "").strip()

        if not normalized_uuid:
            return None

        raw_stations, _server = await self._request_json(
            path="/json/stations/byuuid",
            parameters={
                "uuids": normalized_uuid,
                "hidebroken": "true",
            },
        )

        if not isinstance(raw_stations, list):
            return None

        for raw_station in raw_stations:
            if not isinstance(raw_station, dict):
                continue

            station = self._normalize_station(raw_station)

            if station is not None:
                return station

        return None

    async def register_station_click(
        self,
        station_uuid: str,
    ) -> bool:
        """
        Meldet Radio Browser, dass eine Station gestartet wurde.

        Dadurch wird die Klickstatistik der öffentlichen Datenbank
        aktualisiert.
        """

        normalized_uuid = str(station_uuid or "").strip()

        if not normalized_uuid:
            return False

        try:
            result, _server = await self._request_json(
                path=f"/json/url/{normalized_uuid}",
                parameters={},
            )
        except RadioBrowserError:
            return False

        if not isinstance(result, dict):
            return False

        return str(
            result.get("ok", "")
        ).strip().lower() == "true"

    async def _request_json(
        self,
        *,
        path: str,
        parameters: dict[str, str | int],
    ) -> tuple[Any, str]:
        """Probiert mehrere Radio-Browser-Server nacheinander aus."""

        servers = list(self.API_SERVERS)
        random.shuffle(servers)

        errors: list[str] = []

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json",
        }

        timeout = httpx.Timeout(
            timeout=self.timeout,
            connect=min(self.timeout, 4.0),
        )

        async with httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            for server in servers:
                url = f"{server}{path}"

                try:
                    response = await client.get(
                        url,
                        params=parameters,
                    )

                    response.raise_for_status()
                    return response.json(), server

                except (
                    httpx.HTTPError,
                    ValueError,
                ) as error:
                    errors.append(
                        f"{server}: {error}"
                    )

        error_summary = "; ".join(errors)

        raise RadioBrowserError(
            "Die Online-Senderdatenbank ist momentan "
            "nicht erreichbar."
            + (
                f" Technische Details: {error_summary}"
                if error_summary
                else ""
            )
        )

    @staticmethod
    def _normalize_station(
        station: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Überführt einen Radio-Browser-Eintrag in das TMBA-Format."""

        external_id = str(
            station.get("stationuuid") or ""
        ).strip()

        name = str(
            station.get("name") or ""
        ).strip()

        resolved_url = str(
            station.get("url_resolved") or ""
        ).strip()

        original_url = str(
            station.get("url") or ""
        ).strip()

        stream_url = resolved_url or original_url

        if not name or not stream_url:
            return None

        tags = [
            tag.strip()
            for tag in str(
                station.get("tags") or ""
            ).split(",")
            if tag.strip()
        ]

        languages = [
            language.strip()
            for language in str(
                station.get("language") or ""
            ).split(",")
            if language.strip()
        ]

        return {
            "external_id": external_id,
            "provider": "radio-browser",
            "name": name,
            "stream_url": stream_url,
            "original_url": original_url,
            "homepage": str(
                station.get("homepage") or ""
            ).strip(),
            "logo_url": str(
                station.get("favicon") or ""
            ).strip(),
            "country": str(
                station.get("country") or ""
            ).strip(),
            "country_code": str(
                station.get("countrycode") or ""
            ).strip().upper(),
            "state": str(
                station.get("state") or ""
            ).strip(),
            "languages": languages,
            "tags": tags,
            "codec": str(
                station.get("codec") or ""
            ).strip().upper(),
            "bitrate": RadioBrowserService._to_int(
                station.get("bitrate"),
                0,
            ),
            "votes": RadioBrowserService._to_int(
                station.get("votes"),
                0,
            ),
            "click_count": RadioBrowserService._to_int(
                station.get("clickcount"),
                0,
            ),
            "last_check_ok": RadioBrowserService._to_bool(
                station.get("lastcheckok"),
            ),
            "hls": RadioBrowserService._to_bool(
                station.get("hls"),
            ),
        }

    @staticmethod
    def _to_int(
        value: Any,
        default: int,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        try:
            return int(value) == 1
        except (
            TypeError,
            ValueError,
        ):
            return str(value).strip().lower() in {
                "true",
                "yes",
                "on",
            }


radio_browser_service = RadioBrowserService()