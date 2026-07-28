import json
import time
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ArtworkService:
    """Ermittelt Coverbilder für die verschiedenen TMBA-Quellen."""

    SEARCH_URL = "https://itunes.apple.com/search"
    STATION_LOGOS = {
    "radio paradise": (
        "http://127.0.0.1:8000/"
        "static/station-logos/radio-paradise.svg"
    ),
}

    # Gefundene Cover bleiben 24 Stunden im Cache.
    CACHE_TTL_SECONDS = 24 * 60 * 60

    # Fehlgeschlagene Suchanfragen werden erst nach 10 Minuten wiederholt.
    NEGATIVE_CACHE_TTL_SECONDS = 10 * 60

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, str]] = {}

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value or "").strip().lower().split())

    @staticmethod
    def _split_stream_title(title: str) -> tuple[str, str]:
        """
        Zerlegt typische Webradio-Metadaten:

            Interpret - Titel

        Rückgabe:

            (Interpret, Titel)
        """

        cleaned_title = str(title or "").strip()

        for separator in (" - ", " – ", " — "):
            if separator in cleaned_title:
                artist, track_title = cleaned_title.split(separator, 1)

                return (
                    artist.strip(),
                    track_title.strip(),
                )

        return "", cleaned_title

    def _prepare_metadata(
        self,
        title: str,
        artist: str,
    ) -> tuple[str, str]:
        cleaned_title = str(title or "").strip()
        cleaned_artist = str(artist or "").strip()

        # Bei Webradio enthält title häufig bereits
        # "Interpret - Titel", während artist nur "Live" ist.
        if not cleaned_artist or cleaned_artist.lower() in {
            "live",
            "webradio",
            "unbekannt",
            "unknown",
        }:
            parsed_artist, parsed_title = self._split_stream_title(
                cleaned_title
            )

            if parsed_artist and parsed_title:
                return parsed_title, parsed_artist

        return cleaned_title, cleaned_artist

    def _cache_key(
        self,
        title: str,
        artist: str,
        album: str,
    ) -> str:
        return "|".join(
            (
                self._normalize(title),
                self._normalize(artist),
                self._normalize(album),
            )
        )

    def _get_cached(self, key: str) -> Optional[str]:
        cached_value = self._cache.get(key)

        if cached_value is None:
            return None

        cached_at, cover_url = cached_value

        ttl = (
            self.CACHE_TTL_SECONDS
            if cover_url
            else self.NEGATIVE_CACHE_TTL_SECONDS
        )

        if time.monotonic() - cached_at > ttl:
            self._cache.pop(key, None)
            return None

        return cover_url

    def _store_cached(self, key: str, cover_url: str) -> None:
        self._cache[key] = (
            time.monotonic(),
            str(cover_url or ""),
        )

    @staticmethod
    def _larger_artwork_url(url: str) -> str:
        """
        Versucht, aus der kleinen iTunes-Grafik eine größere Variante
        zu erzeugen. Falls das URL-Muster nicht passt, bleibt die
        Originaladresse unverändert.
        """

        cover_url = str(url or "").strip()

        if not cover_url:
            return ""

        replacements = (
            ("100x100bb", "600x600bb"),
            ("100x100-75", "600x600-75"),
            ("100x100", "600x600"),
        )

        for old_value, new_value in replacements:
            if old_value in cover_url:
                return cover_url.replace(old_value, new_value)

        return cover_url

    def _search_itunes(
        self,
        title: str,
        artist: str,
        album: str,
    ) -> str:
        search_parts = [
            value
            for value in (artist, title, album)
            if str(value or "").strip()
        ]

        if not search_parts:
            return ""

        query = urlencode(
            {
                "term": " ".join(search_parts),
                "media": "music",
                "entity": "song",
                "country": "DE",
                "limit": 5,
            }
        )

        request = Request(
            f"{self.SEARCH_URL}?{query}",
            headers={
                "Accept": "application/json",
                "User-Agent": "TMBA-OS/0.1",
            },
        )

        try:
            with urlopen(request, timeout=3.0) as response:
                payload: dict[str, Any] = json.load(response)

        except (
            HTTPError,
            URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ) as error:
            print(f"Artwork-Suche fehlgeschlagen: {error}")
            return ""

        results = payload.get("results", [])

        if not isinstance(results, list):
            return ""

        for result in results:
            if not isinstance(result, dict):
                continue

            artwork_url = str(
                result.get("artworkUrl100") or ""
            ).strip()

            if artwork_url:
                return self._larger_artwork_url(artwork_url)

        return ""

    def _get_station_logo(
        self,
        station: str,
    ) -> str:
        """Liefert ein lokales Logo für einen bekannten Radiosender."""

        normalized_station = self._normalize(station)

        if not normalized_station:
            return ""

        # Zunächst exakte Übereinstimmung.
        exact_logo = self.STATION_LOGOS.get(normalized_station)

        if exact_logo:
            return exact_logo

        # Einige Sendernamen enthalten Zusätze wie:
        # "Radio Paradise Main Mix".
        for station_key, logo_url in self.STATION_LOGOS.items():
            if station_key in normalized_station:
                return logo_url

        return ""

    def get_cover(
        self,
        *,
        title: str = "",
        artist: str = "",
        album: str = "",
        source: str = "",
        station: str = "",
        existing_cover_url: str = "",
    ) -> str:

        """
        Liefert eine Cover-URL.
        Reihenfolge:
        1. Bereits von der Quelle geliefertes Cover
        2. Cache
        3. iTunes-Musiksuche
        4. Lokales Senderlogo
        5. Leerer String als TMBA-Platzhalter
        """

        current_cover = str(existing_cover_url or "").strip()

        if current_cover:
            return current_cover

        prepared_title, prepared_artist = self._prepare_metadata(
            title=title,
            artist=artist,
        )

        key = self._cache_key(
            title=prepared_title,
            artist=prepared_artist,
            album=album,
        )

        cached_cover = self._get_cached(key)

        if cached_cover is not None:
            return cached_cover

        # Der Parameter source wird bereits mitgeführt,
        # damit später Senderlogos und lokale USB-Cover
        # ergänzt werden können.
        _ = source

        cover_url = self._search_itunes(
            title=prepared_title,
            artist=prepared_artist,
            album=album,
        )

        # Nur wenn kein Titelcover gefunden wurde, wird bei
        # Webradio nach einem bekannten Senderlogo gesucht.
        if not cover_url and self._normalize(source) == "webradio":
            cover_url = self._get_station_logo(station)

        self._store_cached(key, cover_url)

        return cover_url


artwork_service = ArtworkService()
