"""REST API for the central TMBA AudioManager."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tmba.audio.manager import audio_manager

router = APIRouter(prefix="/audio", tags=["Audio"])

class AudioSourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=32)
    force: bool = False

class AudioVolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)

@router.get("/status")
def get_audio_status():
    return audio_manager.get_status()

@router.get("/pipeline")
def get_audio_pipeline_status():
    """Return the complete logical AudioPipeline status."""
    try:
        return audio_manager.get_pipeline_status()
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": (
                    "Der Status der AudioPipeline konnte nicht "
                    f"gelesen werden: {error}"
                ),
            },
        ) from error

@router.post("/source")
def select_audio_source(request: AudioSourceRequest):
    try:
        result = audio_manager.select_source(request.source, force=request.force)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not result.get("success", False):
        raise HTTPException(status_code=409, detail=result)
    return result

@router.post("/play")
def play_audio():
    return _transport_response(audio_manager.play())

@router.post("/pause")
def pause_audio():
    return _transport_response(audio_manager.pause())

@router.post("/stop")
def stop_audio():
    return _transport_response(audio_manager.stop())

@router.post("/previous")
def previous_audio():
    return _transport_response(audio_manager.previous())

@router.post("/next")
def next_audio():
    return _transport_response(audio_manager.next())

@router.post("/volume")
def set_audio_volume(request: AudioVolumeRequest):
    return _transport_response(audio_manager.set_volume(request.volume))

@router.post("/sync")
def synchronize_audio():
    return _transport_response(audio_manager.synchronize())

def _transport_response(result: dict):
    if not result.get("success", False):
        raise HTTPException(status_code=409, detail=result)
    return result
