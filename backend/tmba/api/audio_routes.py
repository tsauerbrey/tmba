"""REST API for the central TMBA AudioManager."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tmba.audio.engine import audio_engine
from tmba.audio.manager import audio_manager
from tmba.audio.test_tone import play_test_tone

router = APIRouter(prefix="/audio", tags=["Audio"])

class AudioSourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=32)
    force: bool = False

class AudioVolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)

class EngineSourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=32)
    force: bool = False

class TestToneRequest(BaseModel):
    frequency_hz: float = Field(default=440.0, ge=20.0, le=20000.0)
    duration_seconds: float = Field(default=3.0, ge=0.1, le=10.0)
    amplitude: float = Field(default=0.20, ge=0.01, le=0.50)

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

@router.post("/testtone")
def test_audio_output(request: TestToneRequest):
    """Play a short, deliberately limited hardware test tone."""
    pipeline = audio_manager.get_pipeline_status()
    pipeline_state = pipeline.get("state")
    if getattr(pipeline_state, "value", pipeline_state) == "running":
        raise HTTPException(
            status_code=409,
            detail="Die AudioPipeline läuft bereits. Wiedergabe zuerst stoppen.",
        )
    try:
        return play_test_tone(
            frequency_hz=request.frequency_hz,
            duration_seconds=request.duration_seconds,
            amplitude=request.amplitude,
        ).to_dict()
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail={"success": False, "error": str(error)},
        ) from error

def _transport_response(result: dict):
    if not result.get("success", False):
        raise HTTPException(status_code=409, detail=result)
    return result

@router.get("/engine")
def get_audio_engine_status():
    return audio_engine.status()

@router.post("/engine/start")
def start_audio_engine():
    return _engine_response(audio_engine.start())

@router.post("/engine/stop")
def stop_audio_engine():
    return _engine_response(audio_engine.stop())

@router.post("/engine/source")
def select_audio_engine_source(request: EngineSourceRequest):
    try:
        result = audio_engine.activate_source(
            request.source,
            force=request.force,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _engine_response(result)

def _engine_response(result: dict):
    if not result.get("success", False):
        raise HTTPException(status_code=409, detail=result)
    return result

