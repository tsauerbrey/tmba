from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from tmba.api.audio_routes import router as audio_router
from tmba.api.network_routes import router as network_router
from tmba.api.online_radio_routes import router as online_radio_router
from tmba.api.routes import router
from tmba.api.system_routes import router as system_router
from tmba.audio.manager import register_default_sources
from tmba.core.config import get_settings

settings = get_settings()
STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title=settings.system.project.name,
    description=settings.system.project.full_name,
    version=settings.system.project.version,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:5174", "http://localhost:5175",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")

register_default_sources()

app.include_router(router)
app.include_router(online_radio_router)
app.include_router(system_router)
app.include_router(network_router)
app.include_router(audio_router)

@app.get("/")
def root():
    return {
        "project": settings.system.project.name,
        "full_name": settings.system.project.full_name,
        "version": settings.system.project.version,
        "health": "/system/health",
        "system_info": "/system/info",
        "network_status": "/network/status",
        "audio_status": "/audio/status",
        "audio_pipeline": "/audio/pipeline",
        "audio_engine": "/audio/engine",
        "docs": "/docs",
    }
