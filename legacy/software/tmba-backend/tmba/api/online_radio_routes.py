from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from pydantic import BaseModel

from tmba.services.radio_browser_service import (
    RadioBrowserError,
    radio_browser_service,
)
from tmba.services.station_service import (
    station_service,
)


router = APIRouter(
    prefix="/webradio/online",
    tags=["Webradio Online"],
)


class OnlineStationImportRequest(BaseModel):
    station_uuid: str
    favorite: bool = False


@router.get("/search")
async def search_online_webradio_stations(
    q: str = Query(
        default="",
        max_length=120,
        description=(
            "Sendername oder Teil des Sendernamens"
        ),
    ),
    country_code: str = Query(
        default="",
        min_length=0,
        max_length=2,
        description=(
            "ISO-Ländercode, zum Beispiel DE"
        ),
    ),
    tag: str = Query(
        default="",
        max_length=80,
        description=(
            "Genre oder Radio-Browser-Tag"
        ),
    ),
    language: str = Query(
        default="",
        max_length=80,
        description="Sprache des Senders",
    ),
    minimum_bitrate: int = Query(
        default=0,
        ge=0,
        le=10000,
        description=(
            "Minimale Bitrate in kbit/s"
        ),
    ),
    limit: int = Query(
        default=30,
        ge=1,
        le=100,
        description=(
            "Maximale Anzahl der Suchergebnisse"
        ),
    ),
):
    """Sucht Sender in der Radio-Browser-Datenbank."""

    try:
        return await (
            radio_browser_service.search_stations(
                query=q,
                country_code=country_code,
                tag=tag,
                language=language,
                minimum_bitrate=minimum_bitrate,
                limit=limit,
            )
        )

    except RadioBrowserError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.get("/stations/{station_uuid}")
async def get_online_webradio_station(
    station_uuid: str,
):
    """Lädt die vollständigen Daten einer Online-Station."""

    try:
        station = (
            await radio_browser_service.get_station(
                station_uuid
            )
        )

    except RadioBrowserError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    if station is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Der Online-Sender wurde nicht gefunden."
            ),
        )

    return {
        "station": station,
    }


@router.post("/stations/import")
async def import_online_webradio_station(
    request: OnlineStationImportRequest,
):
    """
    Übernimmt einen Radio-Browser-Sender dauerhaft
    in die lokale TMBA-Senderliste.
    """

    normalized_uuid = str(
        request.station_uuid or ""
    ).strip()

    if not normalized_uuid:
        raise HTTPException(
            status_code=400,
            detail=(
                "Es wurde keine Sender-ID angegeben."
            ),
        )

    try:
        online_station = (
            await radio_browser_service.get_station(
                normalized_uuid
            )
        )

    except RadioBrowserError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    if online_station is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Der Online-Sender wurde nicht gefunden."
            ),
        )

    try:
        import_result = (
            station_service.import_online_station(
                online_station,
                favorite=request.favorite,
            )
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    return {
        "success": True,
        "created": import_result["created"],
        "station": import_result["station"],
    }