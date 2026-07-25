from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tmba.core.event_bus import event_bus
from tmba.core.player_service import player_service
from tmba.core.source_manager import source_manager
from tmba.services.airplay_service import airplay_service
from tmba.services.bluetooth_service import bluetooth_service
from tmba.services.webradio_service import webradio_service

router = APIRouter()


class VolumeRequest(BaseModel):
    volume: int


class SourceRequest(BaseModel):
    source: str


class SourceAvailabilityRequest(BaseModel):
    available: bool


class AirPlayMetadataRequest(BaseModel):
    title: str = ""
    artist: str = ""
    album: str = ""
    cover_url: str = ""
    duration: int | float = 0
    elapsed: int | float = 0


class AirPlayPlaybackStatusRequest(BaseModel):
    status: str


class AirPlayProgressRequest(BaseModel):
    elapsed: int | float
    duration: int | float | None = None


class BluetoothMetadataRequest(BaseModel):
    title: str = ""
    artist: str = ""
    album: str = ""
    cover_url: str = ""
    duration: int | float = 0
    elapsed: int | float = 0


class BluetoothPlaybackStatusRequest(BaseModel):
    status: str


class BluetoothProgressRequest(BaseModel):
    elapsed: int | float
    duration: int | float | None = None


class WebradioMetadataRequest(BaseModel):
    title: str = ""
    artist: str = ""
    album: str = ""
    cover_url: str = ""
    duration: int | float = 0
    elapsed: int | float = 0


class WebradioPlaybackStatusRequest(BaseModel):
    status: str

class WebradioPlayRequest(BaseModel):
    url: str
    station_name: str = ""


@router.get("/status")
def status():
    return player_service.get_status()


@router.post("/volume")
def set_volume(request: VolumeRequest):
    return player_service.set_volume(request.volume)


@router.post("/source")
def select_source(request: SourceRequest):
    try:
        return player_service.select_source(request.source)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get("/sources")
def list_sources():
    return {
        "active_source": source_manager.get_active_source(),
        "sources": source_manager.list_sources(),
    }


@router.post("/player/refresh")
def refresh_player():
    return player_service.refresh_from_mpd()


@router.post("/player/play")
def play():
    return player_service.play()


@router.post("/player/pause")
def pause():
    return player_service.pause()


@router.post("/player/stop")
def stop():
    return player_service.stop()


@router.post("/player/previous")
def previous():
    return player_service.previous()


@router.post("/player/next")
def next_track():
    return player_service.next()


@router.post("/sources/{source}/availability")
def set_source_availability(
    source: str,
    request: SourceAvailabilityRequest,
):
    try:
        event_bus.publish(
            "source.availability_changed",
            {
                "source": source,
                "available": request.available,
            },
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "active_source": source_manager.get_active_source(),
        "player": player_service.get_status(),
        "sources": source_manager.list_sources(),
    }


@router.get("/sources/{source}/availability")
def get_source_availability(source: str):
    try:
        available = source_manager.is_source_available(source)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "source": source.strip().lower(),
        "available": available,
        "active_source": source_manager.get_active_source(),
    }


@router.get("/airplay/status")
def get_airplay_status():
    return airplay_service.get_status()


@router.post("/airplay/session/start")
def start_airplay_session():
    result = airplay_service.connect_client()

    return {
        "airplay": result["airplay"],
        "player": player_service.get_status(),
    }


@router.post("/airplay/session/end")
def end_airplay_session():
    result = airplay_service.disconnect_client()

    return {
        "airplay": result["airplay"],
        "player": player_service.get_status(),
    }


@router.post("/airplay/metadata")
def update_airplay_metadata(
    request: AirPlayMetadataRequest,
):
    return {
        "airplay": airplay_service.update_metadata(
            title=request.title,
            artist=request.artist,
            album=request.album,
            cover_url=request.cover_url,
            duration=request.duration,
            elapsed=request.elapsed,
        ),
        "player": player_service.get_status(),
    }


@router.post("/airplay/playback-status")
def set_airplay_playback_status(
    request: AirPlayPlaybackStatusRequest,
):
    try:
        airplay_status = airplay_service.set_playback_status(
            request.status
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "airplay": airplay_status,
        "player": player_service.get_status(),
    }


@router.post("/airplay/progress")
def update_airplay_progress(
    request: AirPlayProgressRequest,
):
    return {
        "airplay": airplay_service.update_progress(
            elapsed=request.elapsed,
            duration=request.duration,
        ),
        "player": player_service.get_status(),
    }


@router.get("/bluetooth/status")
def get_bluetooth_status():
    return bluetooth_service.get_status()


@router.post("/bluetooth/session/start")
def start_bluetooth_session():
    result = bluetooth_service.connect_device()

    return {
        "bluetooth": result["bluetooth"],
        "player": player_service.get_status(),
    }


@router.post("/bluetooth/session/end")
def end_bluetooth_session():
    result = bluetooth_service.disconnect_device()

    return {
        "bluetooth": result["bluetooth"],
        "player": player_service.get_status(),
    }


@router.post("/bluetooth/metadata")
def update_bluetooth_metadata(
    request: BluetoothMetadataRequest,
):
    return {
        "bluetooth": bluetooth_service.update_metadata(
            title=request.title,
            artist=request.artist,
            album=request.album,
            cover_url=request.cover_url,
            duration=request.duration,
            elapsed=request.elapsed,
        ),
        "player": player_service.get_status(),
    }


@router.post("/bluetooth/playback-status")
def set_bluetooth_playback_status(
    request: BluetoothPlaybackStatusRequest,
):
    try:
        bluetooth_status = bluetooth_service.set_playback_status(
            request.status
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "bluetooth": bluetooth_status,
        "player": player_service.get_status(),
    }


@router.post("/bluetooth/progress")
def update_bluetooth_progress(
    request: BluetoothProgressRequest,
):
    return {
        "bluetooth": bluetooth_service.update_progress(
            elapsed=request.elapsed,
            duration=request.duration,
        ),
        "player": player_service.get_status(),
    }


@router.get("/webradio/status")
def get_webradio_status():
    return webradio_service.get_status()


@router.post("/webradio/session/start")
def start_webradio_session():
    return {
        "webradio": webradio_service.session_started(),
        "player": player_service.get_status(),
    }


@router.post("/webradio/session/end")
def end_webradio_session():
    return {
        "webradio": webradio_service.session_ended(),
        "player": player_service.get_status(),
    }


@router.post("/webradio/metadata")
def update_webradio_metadata(
    request: WebradioMetadataRequest,
):
    return {
        "webradio": webradio_service.update_metadata(
            title=request.title,
            artist=request.artist,
            album=request.album,
            cover_url=request.cover_url,
            duration=request.duration,
            elapsed=request.elapsed,
        ),
        "player": player_service.get_status(),
    }


@router.post("/webradio/playback-status")
def set_webradio_playback_status(
    request: WebradioPlaybackStatusRequest,
):
    try:
        webradio_status = webradio_service.set_playback_status(
            request.status
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "webradio": webradio_status,
        "player": player_service.get_status(),
    }


@router.post("/webradio/play-station")
def play_webradio_station(
    request: WebradioPlayRequest,
):
    result = webradio_service.play_station(
        url=request.url,
        station_name=request.station_name,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return {
        **result,
        "player": player_service.get_status(),
    }


@router.post("/webradio/play")
def play_webradio():
    result = webradio_service.play()

    if not result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return {
        **result,
        "player": player_service.get_status(),
    }


@router.post("/webradio/pause")
def pause_webradio():
    result = webradio_service.pause()

    if not result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return {
        **result,
        "player": player_service.get_status(),
    }


@router.post("/webradio/stop")
def stop_webradio():
    result = webradio_service.stop()

    if not result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return {
        **result,
        "player": player_service.get_status(),
    }


@router.post("/webradio/sync")
def sync_webradio_from_mpd():
    result = webradio_service.sync_from_mpd()

    if not result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return {
        **result,
        "player": player_service.get_status(),
    }